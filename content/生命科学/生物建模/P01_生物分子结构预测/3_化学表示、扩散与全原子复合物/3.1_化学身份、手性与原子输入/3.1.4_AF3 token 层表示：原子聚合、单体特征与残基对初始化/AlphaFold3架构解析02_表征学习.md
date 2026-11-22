# AlphaFold3 架构解析（二）：表征学习（Representation Learning）

> 本文为 [shenyichong/alphafold3-architecture-walkthrough](https://github.com/shenyichong/alphafold3-architecture-walkthrough)（MIT License）中文版，已在原译文基础上做通顺化与术语统一。配图来自该仓库。

## 模板模块

- 模板模块的输入是什么？
    - token 级配对表示 { z_i_j }，以及包含模板信息的特征 {**f**}。
- 模板特征如何构建？【来自 Algorithm 16 TemplateEmbedder】

    ![image.png](assets/AlphaFold3架构解析/image%2031.png)

    1. 针对模板 t，`b_template_backbone_frame_mask_i_j` 由第 t 个模板在 i 位置和 j 位置的 `template_backbone_frame_mask` 值共同决定：只有当 i 和 j 两个位置都包含足以计算骨架（backbone）的全部原子时，该 mask 才为 1，否则为 0。
    2. 同理，只有当第 t 个模板的 i 位置和 j 位置的 `template_pseudo_beta_mask` 都为 1 时，`b_template_pseudo_beta_mask_i_j` 才为 1，否则为 0。其含义是中心原子（pseudo-beta）在 i 和 j 位置是否有坐标。
    3. `a_t_i_j` 计算第 t 个模板在 i 位置和 j 位置的相关特征：将 `template_distogram`（表示两个 token 之间的距离，形状为 [N_templ, N_token, N_token, 39]）的最后一维、`b_template_backbone_frame_mask_i_j`（1 维标量）、`template_unit_vector`（表示两个 token 之间包含方向的单位向量，形状为 [N_templ, N_token, N_token, 3]）的最后一维，以及 `b_template_pseudo_beta_mask_i_j`（1 维标量）拼接起来，得到一个维度为 44 的向量。
    4. 如果位于 i 位置的 token 和位于 j 位置的 token 不在同一条链上，则 `a_t_i_j` 向量置为全 0 向量。
    5. `a_t_i_j` 再拼接上第 t 个模板在 i 位置的残基类型（one-hot 编码）和 j 位置的残基类型信息，得到维度为 [44+32+32 = 108] 的 `a_t_i_j` 向量。{a_t_i_j} 的形状为 [N_templ, N_token, N_token, 108]。
- 然后针对每一个模板，执行以下相同操作：【来自 Algorithm 16 TemplateEmbedder】

    ![image.png](assets/AlphaFold3架构解析/image%2032.png)

    1. 首先定义一个 `u_i_j` 用于存放计算结果，{u_i_j} 的形状是 [N_token, N_token, c]。
    2. 针对每一个模板进行相同的操作：对 `a_t_i_j` 进行线性变换，从 108 维 → c 维；对 `z_i_j` 先进行 LN，再进行线性变换，从 c_z 维 → c 维。然后将相同的、经变换后的 `z_i_j` 加到每一个模板的 `a_t_i_j` 上，得到 `v_i_j`，维度为 c 维。
    3. 然后将 `v_i_j` 通过 PairformerStack 计算，将结果再加上 `v_i_j` 作为 `v_i_j` 的结果，维度为 c 维。
    4. 最后对 `v_i_j` 进行 LN 之后，对所有模板的结果都加到 `u_i_j` 向量上，维度为 c 维。
- 最后对 `u_i_j` 的结果求平均（除以模板的数量），再做一次激活，然后经过一次线性变换得到最终结果 `u_i_j`，{u_i_j} 的形状为 [N_token, N_token, c]。【来自 Algorithm 16 TemplateEmbedder】

    ![image.png](assets/AlphaFold3架构解析/image%2033.png)

## MSA 模块

![image.png](assets/AlphaFold3架构解析/image%2034.png)

- 此模块的目标：同时更新 MSA 和配对表示（Pair Representation）特征，并让二者相互影响。先通过 Outer Product Mean 让 MSA 表示更新配对表示，然后再使用配对表示，通过 row-wise gated self-attention using only pair bias 来更新 MSA 的表示。最终配对表示经过一系列三角计算并完成更新。
- 输入：
    - MSA 表示（会按行进行 subsample，只随机选取其中少部分样本）
        - f_msa：形状为 [N_msa, N_token, 32]，即原始的 N_msa 条 MSA 样本，每一个位置有 32 种可能性。
        - f_has_deletion：形状为 [N_msa, N_token]，原始信息，指示每个位置左边是否有删除。
        - f_deletion_value：形状为 [N_msa, N_token]，原始信息，指示原始删除计数（Raw deletion counts），大小在 [0,1] 之间。
    - S_inputs_i：初始的 token 级单体序列（single sequence）特征，形状为 [N_token, C_token+65]，这里的 65 是 32+32+1，其中包含了当前 token 的 restype，以及 MSA 的一些特征，包括在 i 位置各个 restype 类型的分布，以及在 i 位置的 deletion mean 值。如果当前 token 没有 MSA 信息，则这 65 维都为 0。
    - token 级配对表示：{z_ij}，形状为 [N_token, N_token, C_z=128]。
- 输出：更新之后的 token 级配对表示：{z_ij}，形状为 [N_token, N_token, C_z=128]。
- 直接看伪代码：

    ![image.png](assets/AlphaFold3架构解析/image%2035.png)

    1. 首先，将 `f_msa_Si`、`f_has_deletion_Si` 以及 `f_deletion_Si` 拼接起来，得到一个 32+1+1=34 的向量：**m_Si**。注意这里的 S 和 i 都是下标，S 表示在 N_msa 中的第 S 行（第 S 个样本），i 表示每一行中的第 i 个位置。
    2. 然后通过 SampleRandomWithoutReplacement 函数对 N_msa 进行 subsample，{S} 代表所有 N_msa 可能的序号集合，而 {s} 代表下采样之后的可能的序号集合。
    3. 然后 **m_si** 代表下采样之后的第 s 个样本、第 i 个位置，对其进行线性变换，将维度从 34 → C_m=64。
    4. 然后加上 {S_inputs_i} 进行线性变换后的结果，得到一个新的 MSA 特征 **m_si**。这里 S_inputs_i 也包含了 MSA 在每一个位置上的相关特征（如果有的话），维度是 C_token+65。
    5. 然后针对 N_block 个 block 进行循环：
        1. 对 MSA 信息 m_si 进行 OuterProductMean 计算，并融合到配对表示（pair representation）中：
            1. 输入 {m_si} 的形状是 [n_msa, N_tokens, C_m]，具体算法如下：

                ![image.png](assets/AlphaFold3架构解析/image%2036.png)

                1. 首先，对 m_si 进行 LN，{m_si} 的形状为 [n_msa, N_tokens, C_m]。
                2. 然后进行线性变换，得到 a_si 和 b_si，线性变换是从 C_m=64 → c=32。
                3. 对于每一个 s，计算 a_si 和 b_sj 的外积，相当于对第 s 个 MSA 样本，通过外积来计算其 i 位置和 j 位置的关系。
                    1. 长度为 c 的向量与长度为 c 的向量做外积，得到一个 [c, c] 矩阵；
                    2. 然后将 s 个 [c, c] 矩阵按每个位置 (i,j) 求平均；
                    3. 最后将这个矩阵展平成一维向量，得到 o_ij，形状为 c*c。
                4. 最后再经过一次线性变换，将 c*c → c_z=128 维，得到最终的 z_ij，即通过 MSA 计算得到的位置之间的信息。

                注 1：这里通过 OuterProductMean 方法，将 MSA 的表示融合到配对表示中。对同一条 MSA 序列，通过外积的方式得到其任意两个位置之间的关系，然后对所有 MSA 序列在这两个位置的结果求平均，得到任意两个位置之间在进化上的关系信息，并融合到配对表示中。

                注 2：注意这里仅在进化序列内部进行计算，而进化序列之间的信息只通过一次平均的方式融合在一起，避免了 AF2 中进化序列之间复杂的计算。

        2. 使用更新后的配对表示和 m_si 来更新 m_si（MSA 特征）：MSA row-wise gated self-attention using only pair bias
            1. 输入是 {m_si}，形状是 [n_msa, N_tokens, C_m=64]，{z_ij} 的形状是 [N_token, N_token, C_z=128]。输出是 {m_si}，形状是 [n_msa, N_tokens, C_m=64]。具体算法如下：

                ![image.png](assets/AlphaFold3架构解析/image%2037.png)

                1. 首先对 MSA 特征 m_si 进行 LN。
                2. 然后对 m_si 进行多头线性变换，得到 H_head 个头 v_h_si，线性变换维度从 C_m → c。
                3. 对配对表示特征 z_ij 首先进行 LN，然后进行多头线性变换，得到 b_h_ij，维度从 C_z → 1。
                4. 对 m_si 进行多头线性变换，维度从 C_m → c，然后计算其 sigmoid 值，得到 g_h_si，用于后续 gating。
                5. 对 b_h_ij 沿着 j 方向做 softmax，得到权重 w_h_ij，维度为 1。
                6. 这里比较难理解的是如何得到 o_h_si：这里 v_h_sj 和 w_h_ij 在 j 方向上按元素相乘，然后加起来得到 o_h_si 的中间结果。
                    1. 即对于 {w_h_ij} 这个形状为 [N_token, N_token] 的矩阵，取其第 i 行的元素 [N_token]。
                    2. 对 {v_h_sj} 这个形状为 [n_msa, N_token, c] 的矩阵，取其第 s 行的元素 [N_token, c]。
                    3. 将其按元素相乘并加总起来，得到一个 c 维向量，其位置对应原 {m_si} 矩阵的第 s 行、第 i 列。
                    4. o_h_si 再在 c 维度上按元素乘以 g_h_si，进行 gating。
                7. 最后针对 o_h_si，将其 H_head 个头 concat 起来，得到一个 c*H_head 长的向量，然后经过线性变换后得到最终结果 m^_si。
            2. 注意，这部分是通过配对表示来更新 MSA 的表示，更新方式是对每一条 MSA 序列来说，其更新相互独立。然后使用配对表示中的位置之间的关系来构建权重，相当于对 m_si 中的每一个位置做了一次 self-attention，引入了配对表示中的信息。
        3. {m_si} 再经过一层过渡层（transition）后，作为下一个 block 的 {m_si} 输入。
        4. 配对表示 {z_ij} 经过一系列的三角计算和过渡层后，再作为下一个 block 的 {m_si} 输入。

## Pairformer 模块

![image.png](assets/AlphaFold3架构解析/image%2038.png)

- 首先了解 Pairformer 这部分模块主要做了什么事情：配对表示会进行三角更新和三角注意力计算，并且用于更新单体表示。和 AF2 不同的是，这里单体表示不会去影响配对表示。
- 输入输出：输入是 token 级配对表示 {z_ij} 和 token 级单体表示 {s_i}，它们的形状分别是 [N_token, N_token, C_z=128] 和 [N_token, C_s=C_token=384]。
- 为什么要关注三角关系？（Why look at Triangles？）
    - 三角不等式指出：三角形任意两边之和大于第三边。而在配对表示中表征了任意两个 token 之间的关系，为简化理解，我们可以将其看作序列中任意两个氨基酸之间的距离，那么 z_ij 代表 i 氨基酸和 j 氨基酸之间的距离；已知 z_ij=1、z_jk=1，我们就可以知道 z_ik < 2。这样我们就能通过 z_ij 和 z_jk 的距离来确定 z_ik 的距离范围，也就是说，可以通过 z_ij 和 z_jk 来约束 z_ik 可能的值，因此三角更新和三角注意力机制就是为了将这种几何约束编码到模型之中。
    - 所以，z_ij 的值可以通过获取所有可能的 k 所对应的（z_ik，z_jk）来进行更新。由于真实情况是，z_ij 并不仅仅包含距离信息，它代表了 i 和 j 之间的关系信息，因此它也是有方向的，z_ij 和 z_ji 表示的含义并不一样。
    - 并且基于图（graph）计算理论，将三角关系中用于更新 z_ij 这一条边的另外两条边的方向分为 incoming 和 outgoing。则针对 z_ij，

        ![image.png](assets/AlphaFold3架构解析/image%2039.png)

        - 其 outgoing edges 是：z_ik, z_jk
        - 其 incoming edges 是：z_ki, z_kj
    - 为什么要区分 outgoing edges 和 incoming edges？为什么不能混用？→ 当前暂时的理解是，两条边同时从 i 和 j 指向 k，或者同时从 k 指向 i 和 j，因为 edge 是有方向性的：同时从 i 和 j 指向 k（或相反），这两条边的物理含义是一致的，就是 i 和 j 对 k 的关系（或相反），更加便于模型准确地建模。（这里的理解还是不够透彻，等有机会再梳理。）
- 接下来看看具体是如何计算 triangular update 和 triangular attention 的：
    - Triangular Update（三角更新）
        - Outgoing：
            - 具体的算法实现：

                ![image.png](assets/AlphaFold3架构解析/image%2040.png)

                1. z_i_j 这个向量自己进行 LayerNorm，即在 c_z 维度上进行归一化。
                2. z_i_j 进行线性变换，转换为维度为 c=128 的向量，然后对每一个位置计算 sigmoid 值，再与另外一个经过线性变换的向量按元素相乘，得到一个 a_i_j 或 b_i_j，维度是 c 维。
                3. 然后还是对 z_i_j 先进行线性变换（变换前后维度不变，仍是 c_z），再计算 sigmoid，得到 g_i_j，维度是 c_z，这个向量用于 gating。
                4. 最后计算 Triangular Update：要更新 z_i_j，需要从 a_i_k 和 b_j_k 的计算中得到（k 有 N_token 个选择）。具体方法是：从 {a_i_j} 中选取 i 行，得到 {a_i}（有 N_token 个向量），从 {b_i_j} 中选取 j 行，得到 {b_j}（有 N_token 个向量）；然后对 {a_i} 和 {b_j} 中的第 k 个元素计算按元素相乘，得到一个 c 维向量，再将所有 N_token 个向量加起来，得到一个 c 维向量，然后进行 LayerNorm 计算，最后进行线性变换得到一个 c_z 维度的向量；最后按元素乘以 g_i_j，得到最终的 z_i_j 结果。
            - 图示化解释：

                ![image.png](assets/AlphaFold3架构解析/image%2041.png)

        - Incoming：
            - 具体的算法实现：

                ![image.png](assets/AlphaFold3架构解析/image%2042.png)

                - 注意这里的主要变化，就是计算的是 a_k_i 和 b_k_j，即从列的角度进行计算，和前面的计算方法刚好对称。从下面的图示也可以明显地看出来。
            - 图示化解释：

                ![image.png](assets/AlphaFold3架构解析/image%2043.png)

    - Triangular Attention（三角注意力）
        - Triangular Attention（Starting Node 对应 outgoing edges）
            - 具体算法实现：

                ![image.png](assets/AlphaFold3架构解析/image%2044.png)

                1. 首先对 z_i_j 进行 LayerNorm 归一化处理。
                2. 针对 N_head 个头中的特定 h 头，对 z_i_j 进行不同的线性变换，得到 q_h_i_j、k_h_i_j、v_h_i_j，维度变换均为 c_z → c。
                3. 针对 N_head 个头中的特定 h 头，对 z_i_j 进行线性变换，得到 b_h_i_j。维度变换为 c_z → 1。
                4. 针对 N_head 个头中的特定 h 头，对 z_i_j 先进行线性变换，维度变换为 c_z → c，然后对每一个元素计算 sigmoid 值，得到 g_h_i_j，用于后续 gating。
                5. 计算 Triangular Attention 第一步：计算 attention score。对 q_h_i_j 和 k_h_i_k 计算点积，然后除以 sqrt(c)，再加上 b_h_j_k 这个维度为 1 的值，得到的标量再在 k 维度上计算 softmax，得到 k 位置上的 attention score a_h_i_j_k。这是一个标量值，也可以理解为一个权重值，用于后续乘以 value。
                6. 计算 Triangular Attention 第二步：计算 (i,j) 位置上的 attention 结果。通过 a_h_i_j_k 与 v_h_i_k 的加权和（weighted sum），得到 attention 在 (i,j) 位置上的值，这是一个维度为 c 的向量；然后与 g_h_i_j 按元素相乘，得到经过 gating 的 attention 向量 o_h_i_j，维度也为 c。
                7. 最后针对 {i,j} 位置的值，将多头进行合并：首先按照 h 个多头在最后一个特征维度上拼接，维度变化为 c → h*c；然后再进行一次线性变换，将维度从 h*c → c，得到最终结果 z_i_j。
            - 图示化解释：

                ![image.png](assets/AlphaFold3架构解析/image%2045.png)

                - 这里注意，其实这里的 Triangular Attention 就是一种 Axial Attention 的变种，增加了 b_j_k 作为偏置（bias），并增加了 gating 机制。但如果抛开这两个新增特性，它其实相当于按行做 self-attention。
        - Triangular Attention（Ending Node 对应 incoming edges）
            - 具体算法实现

                ![image.png](assets/AlphaFold3架构解析/image%2046.png)

                - 这里的主要区别在于计算 Triangular Attention 的方法：
                    1. 使用 q_h_i_j 和 k_h_k_j 来计算 attention score，然后再加上 b_h_k_i 这个偏置，作为 a_h_i_j_k 的结果。这里需要注意的是，q_h_i_j 是和 k_h_k_j 而不是和 k_h_k_i 求点积，加上的是 b_h_k_i 而不是 b_h_k_j。原因我猜测是为了方便计算 Axial Attention，否则就不是基于列的 self-attention 了。具体可见下面图示。
            - 图示化解释

                ![image.png](assets/AlphaFold3架构解析/image%2047.png)

                - 原来的图解是错误的，其并没有忠实按照官方文档中的实现进行图示；红色框部分修改了原来图中的错误标注。

- 最后看看含配对偏置的单体注意力（Single Attention with pair bias）如何实现。
    - 输入是 token 级单体表示 {s_i} 和 token 级配对表示 {z_i_j}，输出是 {s_i}。
    - 主要使用 {z_i_j} 作为偏置，加入到 {s_i} 的 self-attention 计算中；同时 {s_i} 的 self-attention 中也增加了 gating 机制。
    - 具体算法伪代码实现为：

        ![image.png](assets/AlphaFold3架构解析/image%2048.png)

        - 单体表示 {s_i} 进行归一化计算。
        - 从 {s_i} 计算特定 h 头的 q、k、v 表示：q_h_i、k_h_i、v_h_i 都经过了线性变换，从 c_token → c。
        - 从配对表示 {z_i_j} 中计算一个偏置值，准备应用在 {s_i} 的 self-attention 中：首先对 {z_i_j} 进行归一化，然后进行线性变换，维度从 c_z → 1，得到 b_h_i_j。
        - 使用 {s_i} 计算后续用于 gating 的值：先对 {s_i} 进行线性变换 c_token → c，然后对其中每一个元素计算 sigmoid 值，得到 g_h_i。
        - 然后计算 attention，实际上就是正常的 self-attention，只是在计算 attention score 时加入了来自配对表示的偏置值 b_h_i_j，从而得到标量 A_h_i_j。
        - 然后使用 v_h_j 对每一个 j 乘以 A_h_i_j 并求和，得到一个经过加权和（weighted sum）的向量，然后再按元素乘 g_h_i，得到特定 h 头上的 attention 结果，然后将结果按最后一维拼接起来，并最终通过一个线性变换，得到经过 attention 之后的 {s_i} 结果，维度为 c_token。
    - 具体的图示化解释如下：

        ![image.png](assets/AlphaFold3架构解析/image%2049.png)
