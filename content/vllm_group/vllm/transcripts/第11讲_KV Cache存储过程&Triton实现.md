# KV Cache存储过程&Triton实现 原始文稿（图-字幕分栏）

| 字幕文本 | 画面 |
| :--- | ---: |
| 哈喽大家好，今天给大家分享 MiniVLLM 中关于 KV cache 那一部分的代码和案例。 [【跳转到 00:00】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=0) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00000.jpg" width="9000"> |
| 我们之前已经讲过 prefill 以及 decode 了，还剩一点 KV cache。 [【跳转到 00:07】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=7) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00007.jpg" width="9000"> |
| KV cache 相对于 prefill 以及 decode 要简单很多。 [【跳转到 00:12】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=12) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00012.jpg" width="9000"> |
| 我们还是来看，当前在 attention 里，还是和上次一样的 commit。 [【跳转到 00:17】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=17) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00017.jpg" width="9000"> |
| 今天要讲的部分还是 attention interface 内部的事情， [【跳转到 00:22】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=22) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00022.jpg" width="9000"> |
| 也就是内部的 QKV cache，实际上就是 QKV。 [【跳转到 00:27】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=27) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00027.jpg" width="9000"> |
| 我们 QKV 处理完之后传入 attention interface，然后开始做 KV cache。 [【跳转到 00:32】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=32) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00032.jpg" width="9000"> |
| 我们来看一下，此时前向传播已经拿到了 QKV， [【跳转到 00:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=38) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00038.jpg" width="9000"> |
| 也就是这一部分已经计算完了，然后进入 attention interface。 [【跳转到 00:43】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=43) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00043.jpg" width="9000"> |
| 进来之后第一步就是判断 KV cache 是否存在。 [【跳转到 00:48】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=48) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00048.jpg" width="9000"> |
| 因为 KV cache 本质上也是一个张量、在内存中已经分配好了，所以他判断当前 QKV cache 是否已经分配完。 [【跳转到 00:53】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=53) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00053.jpg" width="9000"> |
| 只要分配了，并且 slot_mapping 存在，就会进入 KV cache。这个 slot_mapping 就是：比如当前 batch 传入了 30 个 token，那这 30 个 token 就会有 30 个 slot_mapping，每个 token 对应它应该存放的位置。 [【跳转到 00:59】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=59) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00059.jpg" width="9000"> |
| 就是这个 slot_mapping。这里做一个形状判断，做一次 reshape：如果传进来的 K、V 维度是 4，就降成 3 维——第一维是 token 数量，第二维是头的数量，第三维是头的维度。 [【跳转到 01:24】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=84) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00084.jpg" width="9000"> |
| 然后做一个 contiguous。做完这些之后，会直接访问 `store_kvcache` 去做一个 KV cache 的存储。好，接下来继续讲。 [【跳转到 01:49】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=109) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00109.jpg" width="9000"> |
| 这个待会我们后面再讲 `store_kvcache`。 [【跳转到 02:01】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=121) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00121.jpg" width="9000"> |
| 显存分配这一块，在 prefill 那一部分其实已经讲过了。 [【跳转到 02:06】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=126) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00126.jpg" width="9000"> |
| 这里简单略过一下。以我的显卡为例，整个 HBM 是 8G，其中约 2.23G 用于存放 Qwen3-0.6B 模型，实际可用于分配 KV cache 的空间只有 4GB。 [【跳转到 02:11】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=131) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00131.jpg" width="9000"> |
| 这 4GB 会怎么分配？一半拿去存 K， [【跳转到 02:29】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=149) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00149.jpg" width="9000"> |
| 一半拿去存 V，这个没啥好说的。 [【跳转到 02:34】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=154) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00154.jpg" width="9000"> |
| 然后根据我们存的块大小，比如块大小为 8，就把所有空间除以「以 8 个 token 为单位的块」的大小。因为每个 token 有 K 和 V 两个维度，每个 K、V 有 8 个头， [【跳转到 02:39】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=159) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00159.jpg" width="9000"> |
| 假设每个头维度是 16 维，那就用整个可用空间 [【跳转到 03:01】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=181) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00181.jpg" width="9000"> |
| 除以存放每个 token KV 的实际容量，再乘以 8（block_size 是 8），算出所有可划分的块，最后得到一个块的数量。内存中 [【跳转到 03:14】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=194) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00194.jpg" width="9000"> |
| 就会被划分成一个个块。基本原理就是这样。然后我们来看下面的 `store_kvcache`。 [【跳转到 03:29】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=209) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00209.jpg" width="9000"> |
| `store_kvcache` 传入了几个参数， [【跳转到 03:34】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=214) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00214.jpg" width="9000"> |
| 很简单，就是 K、V， [【跳转到 03:39】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=219) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00219.jpg" width="9000"> |
| 以及 k_cache、v_cache，以及 slot_mapping 和 block_size。 [【跳转到 03:44】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=224) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00224.jpg" width="9000"> |
| 来看内部：把形状参数提出来，第一个是 token_num，头的数量是 8，头的维度是 16（这里 8 和 16 只是举例，实际 MiniVLLM 里不是这么多）。 [【跳转到 03:49】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=229) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00229.jpg" width="9000"> |
| 对 KV 做了一个 contiguous（之前已经做过了），这里做了一个冗余判断，也做了一个断言，还有 slot_mapping 的断言：slot_mapping 的数量 [【跳转到 04:12】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=252) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00252.jpg" width="9000"> |
| 一定等于 token 的数量。这里我细讲一下 slot_mapping 具体指什么，举个例子。 [【跳转到 04:20】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=260) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00260.jpg" width="9000"> |
| 这三个序列实际上就是我们一个 batch， [【跳转到 04:28】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=268) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00268.jpg" width="9000"> |
| 一个 batch 可能一次性输入三个序列，经过 tokenizer 之后变成词向量。 [【跳转到 04:33】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=273) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00273.jpg" width="9000"> |
| 对于第一个 sequence0，长度中等，token_num 等于 9（这里词源是随便写的，真实情况不一定），相当于这个句子最后会被划成 9 个 token；第二个 sequence1 长一点， [【跳转到 04:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=278) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00278.jpg" width="9000"> |
| token 自然长一点，我设成 18 个；第三个 sequence2 最短，token_num 等于 4，经过 tokenizer 后可能只有 4 个。在这个前提下，拿到 token 化之后的序列， [【跳转到 05:03】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=303) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00303.jpg" width="9000"> |
| MiniVLLM 中有一个 scheduler，它会为每个序列分配一个 block_table，并且用一个 slot_mapping 存储每个 token 应该存放的位置。block_table 怎么来的？还是看这个—— [【跳转到 05:18】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=318) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00318.jpg" width="9000"> |
| 假设这是之前讲 decode 时画的图：物理 KV cache 可能是这样，内存中分了从 B0 一直到 B2104 共 2000 多个块。 [【跳转到 05:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=338) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00338.jpg" width="9000"> |
| block_table 初始化时，这 2000 多个块里没有存放任何东西。 [【跳转到 05:55】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=355) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00355.jpg" width="9000"> |
| 这时来了三个序列，scheduler 根据序列长度——比如第一个序列 token_num 是 9，9 需要多少个 block 存储呢？9÷8（8 是 block_size）向上取整等于 2，scheduler 就知道存 sequence0 需要两个 block，于是分配 [【跳转到 06:00】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=360) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00360.jpg" width="9000"> |
| B0 和 B1 去存放。所以 sequence0 的 block_table 实际上是 0 和 1。同理 sequence1，token_num 是 18，18÷8 向上取整等于 3，存 sequence1 需要三个 block， [【跳转到 06:25】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=385) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00385.jpg" width="9000"> |
| 因为 B0、B1 已经分配了，就从 B2、B3、B4 里选，作为 sequence1 的 block_table，即 2、3、4。sequence2 距离很短，只有 4，4÷8 向上取整等于 1，只需分配一个， [【跳转到 06:50】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=410) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00410.jpg" width="9000"> |
| 就会把 B5 分配给 sequence2。 [【跳转到 07:15】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=435) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00435.jpg" width="9000"> |
| 知道每个序列的 block_table 之后，scheduler 还会为每个序列中的每个 token 计算一个 slot_mapping。slot_mapping 的意思是：虽然我知道这个序列需要两个 block 存储，但还需要知道每个 token 具体应该存放在块里的哪个位置——因为每个块可以存放 8 个 token。所以需要一个 slot_mapping。我们来看这个案例，这里是按行显示的， [【跳转到 07:40】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=460) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00460.jpg" width="9000"> |
| 从 B0 到 B6（没画完）。对第一个序列，存放的这些 token 占用两个块 B0 和 B1，从 0、1、2、3……一直到 T8。对 sequence1 也一样。需要注意 sequence1 的 slot_mapping 初始位置是 16，因为它是从 B2 开始的， [【跳转到 08:05】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=485) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00485.jpg" width="9000"> |
| 前面跳过了两个 block，所以从第 16 开始。可以看到 B1 其实没有存满，这是未来在 decode 阶段会往里边填的。这就和之前讲的 decode 阶段呼应上了。理解 slot_mapping 之后，我们就可以来看—— [【跳转到 08:30】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=510) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00510.jpg" width="9000"> |
| 继续看这个网格划分。这里我举了个例子，待会先讲代码， [【跳转到 08:54】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=534) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00534.jpg" width="9000"> |
| 先讲 Triton 算子，然后再看例子。先来看网格划分。 [【跳转到 09:03】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=543) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00543.jpg" width="9000"> |
| 这三个序列一共是 9 + 8 + 9 + 10—— [【跳转到 09:08】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=548) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00548.jpg" width="9000"> |
| 8 + 4 等于 31，所以这里 grid 的 token_num 就是 [【跳转到 09:13】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=553) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00553.jpg" width="9000"> |
| 31，头维度是 8，所以分配 31 × 8。 [【跳转到 09:19】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=559) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00559.jpg" width="9000"> |
| 整体布局就是这样：一共 31 行，每行代表一个 token，每列代表一个头，一共 8 个头。所以就是 31×8，240 多个网格。我们来看每个网格中 [【跳转到 09:24】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=564) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00564.jpg" width="9000"> |
| 具体怎么执行任务——每个网格中 [【跳转到 09:48】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=588) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00588.jpg" width="9000"> |
| 其实就是运行一个 Triton 算子。我们现在来看 Triton 算子。 [【跳转到 09:53】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=593) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00593.jpg" width="9000"> |
| 还是先从代码看。Triton 算子 [【跳转到 09:58】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=598) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00598.jpg" width="9000"> |
| 传入了五个指针，分别是 K、V 的指针、k_cache、v_cache 的指针，以及 slot_mapping 的指针。对于 slot_mapping， [【跳转到 10:03】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=603) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00603.jpg" width="9000"> |
| 它在内存中存放的时候是这样的， [【跳转到 10:13】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=613) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00613.jpg" width="9000"> |
| 原本我们看的是有界限的，但实际内存中它的指针指向第 0 个， [【跳转到 10:18】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=618) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00618.jpg" width="9000"> |
| 而且内存中是连续的，没有一个严格的界限， [【跳转到 10:23】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=623) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00623.jpg" width="9000"> |
| 就是一整个连续的。 [【跳转到 10:32】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=632) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00632.jpg" width="9000"> |
| 然后 KV 头是 8，头维度是 16，block_size 是 8，这是初始化条件。 [【跳转到 10:37】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=637) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00637.jpg" width="9000"> |
| 继续看，首先获取一个 token_id。比如 [【跳转到 10:49】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=649) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00649.jpg" width="9000"> |
| 当前处理的是最后一个 token 的最后一个头， [【跳转到 10:54】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=654) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00654.jpg" width="9000"> |
| 假设在这个块上执行算子的，当前 token_id 算出来：先取 program_id(0)， [【跳转到 10:59】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=659) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00659.jpg" width="9000"> |
| 取出来就是 30，当前 token_id 就是 30。对应看这边， [【跳转到 11:04】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=664) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00664.jpg" width="9000"> |
| 这就是实际内存中的 KV cache—— [【跳转到 11:13】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=673) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00673.jpg" width="9000"> |
| 因为我们 KV 只传了指针， [【跳转到 11:18】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=678) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00678.jpg" width="9000"> |
| 所以这里会拿到两个指向 KV 的指针，指向 KV 第一个 token、第一个头的第一个值。 [【跳转到 11:23】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=683) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00683.jpg" width="9000"> |
| （KV 没画完，） [【跳转到 11:33】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=693) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00693.jpg" width="9000"> |
| 实际上每个 token 打开都是一个 8×16 的张量，即 8 个头、每个头 16 维，这个意思要明白。继续看， [【跳转到 11:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=698) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00698.jpg" width="9000"> |
| 这里取出 slot_id：用 slot_mapping 的指针加上 token_id（刚才取出来是 30），在 slot_mapping 中就是这里。 [【跳转到 11:56】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=716) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00716.jpg" width="9000"> |
| slot_mapping 指针一开始指向这里，加上 30 就跳到最后一个，取出最后一个的 slot_id，就是 43。 [【跳转到 12:08】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=728) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00728.jpg" width="9000"> |
| 取出 slot_id 之后， [【跳转到 12:33】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=753) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00753.jpg" width="9000"> |
| 先做一个判断，然后计算 block_id。block_id 是算当前第 30 个 token 应该存放在哪个 block 中：直接用 43 除以 block_size（8），地板除，等于 5， [【跳转到 12:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=758) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00758.jpg" width="9000"> |
| 说明当前 token 应该存放在 B5 上，对应的 block_id 就是 5。接下来又算 block_offset，即这个 token 应该存放在 B5 中的哪个位置， [【跳转到 13:03】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=783) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00783.jpg" width="9000"> |
| 用取余：43 对 8 取余等于 3（UP 主口述中一度说成 4/5，实际应为 3）。所以这个 token [【跳转到 13:28】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=808) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00808.jpg" width="9000"> |
| 应该存放在 B5 的 [【跳转到 13:33】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=813) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00813.jpg" width="9000"> |
| 存放在第三个位置（从 0 开始计数 0、1、2、3）。OK，然后我们继续来看。 [【跳转到 13:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=818) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00818.jpg" width="9000"> |
| 第 3 个位置（从 0 开始计数 0、1、2、3），存放在这个位置。OK，继续看。 [【跳转到 13:43】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=823) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00823.jpg" width="9000"> |
| 这里是 30，这里是 43， [【跳转到 13:54】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=834) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00834.jpg" width="9000"> |
| block_id 是 5，block_offset 是 3。然后再算我们在计算的是哪一个头——因为每个块 [【跳转到 13:59】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=839) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00839.jpg" width="9000"> |
| 只针对一个头处理，这里有 8 个头 [【跳转到 14:09】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=849) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00849.jpg" width="9000"> |
| （头维度是 8），所以 K 的 index 就是当前处理哪个头。 [【跳转到 14:14】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=854) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00854.jpg" width="9000"> |
| 当前处理的应该是最后一个头，这里读出来是 7， [【跳转到 14:19】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=859) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00859.jpg" width="9000"> |
| 即 H7，处理最后一个头。然后做了一个拓展， [【跳转到 14:24】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=864) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00864.jpg" width="9000"> |
| 从 0 开始展开， [【跳转到 14:30】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=870) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00870.jpg" width="9000"> |
| 方便之后取这一整个头的所有参数。然后最关键的来了，看这个 `input_offset`—— [【跳转到 14:38】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=878) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00878.jpg" width="9000"> |
| 它用在后面读 K、V 数据的时候，用 K、V 的指针加上 input_offset 就可以取出当前块 [【跳转到 14:50】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=890) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00890.jpg" width="9000"> |
| 具体对应的头、具体要取哪些参数。 [【跳转到 15:02】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=902) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00902.jpg" width="9000"> |
| 具体看 input_offset 怎么做： [【跳转到 15:07】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=907) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00907.jpg" width="9000"> |
| 以这个为例，处理的是最后一个 token 的最后一个头， [【跳转到 15:14】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=914) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00914.jpg" width="9000"> |
| 要取出的是这些数字。一开始指针指向 K， [【跳转到 15:19】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=919) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00919.jpg" width="9000"> |
| 传入 Triton 算子的所有 K、V 指针都指向头位置。 [【跳转到 15:24】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=924) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00924.jpg" width="9000"> |
| 第一步先把前面所有 token 跳过去： [【跳转到 15:29】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=929) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00929.jpg" width="9000"> |
| 拿到 token_id 是 30，30 乘以头的数量、再乘以头维度， [【跳转到 15:34】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=934) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00934.jpg" width="9000"> |
| 就可以直接从指针指向 K30。跳过 token 后， [【跳转到 15:39】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=939) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00939.jpg" width="9000"> |
| 指针指向 K30 的第一个头，还需要跳过头：当前是最后一个头，用 7×16（头维度），跳过前面七个头。 [【跳转到 15:44】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=944) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00944.jpg" width="9000"> |
| 再加上 head offset， [【跳转到 15:58】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=958) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00958.jpg" width="9000"> |
| 即当前加上 0~15。 [【跳转到 16:13】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=973) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00973.jpg" width="9000"> |
| 这里相当于做了一个维度拓展：原本指针跳过头之后指向 H7， [【跳转到 16:18】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=978) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00978.jpg" width="9000"> |
| 但实际只指向 H7 的第一个值，还需要加上一个 0~15 [【跳转到 16:24】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=984) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00984.jpg" width="9000"> |
| 的嵌入维度偏移， [【跳转到 16:29】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=989) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00989.jpg" width="9000"> |
| 让指针指向所有这些数字，这样就能把所有 input_offset 取出来， [【跳转到 16:34】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=994) | <img src="img/第11讲_KV Cache存储过程&Triton实现/00994.jpg" width="9000"> |
| （此区间无字幕） [【跳转到 16:44】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1004) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01004.jpg" width="9000"> |
| 把整个头取出来。这就是 input_offset 做的事情。K、V 就可以通过 input_offset 直接取出来。取出来之后还要存进去，所以还需要算一个 cache offset。 [【跳转到 16:49】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1009) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01009.jpg" width="9000"> |
| cache offset 实际上一样。假设内存中的 cache 是这样的： [【跳转到 17:03】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1023) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01023.jpg" width="9000"> |
| 这是 k_cache、这是 v_cache，有 2000 多个 block。当前这个 token 应该存放在哪个位置， [【跳转到 17:08】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1028) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01028.jpg" width="9000"> |
| 需要通过 cache offset 计算。首先需要跳过 block：刚才算出 slot_id 是 43，对应最后一个 token，43÷8 算出当前应该存的 block 是 B5，再用 43 对 8 取余算出是 3，实际上应该存放在 B5 的 [【跳转到 17:14】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1034) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01034.jpg" width="9000"> |
| 第 3 个位置（0、1、2、3），存放在这里。存放时，因为每个 block 里有 8 个 token，每个 token 有 8 个头，每个头有 16 个参数需要存放， [【跳转到 17:39】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1059) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01059.jpg" width="9000"> |
| 所以怎么让指针从 B0、V0 的第一个位置指向这个块的具体头呢？ [【跳转到 18:04】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1084) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01084.jpg" width="9000"> |
| 通过 cache offset 去找。首先跳 block： [【跳转到 18:25】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1105) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01105.jpg" width="9000"> |
| block_id 刚才算出来是 5，5×block_size×8，即 5×8 再乘以头的维度、头嵌入维度，相当于把前面五个 block 跳过去。跳过去之后，前面还有三个 token 需要跳过，所以接下来加上这个值， [【跳转到 18:30】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1110) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01110.jpg" width="9000"> |
| 用于跳过 token。token 的 block_offset 刚才是 3，即前面三个 token，每个 token 有 8 个头，再乘以嵌入维度，所以会跳过三个 token。现在指针就指向 B5 的第四个 token。但这时还需要跳过头，因为要存放的位置是最后一个头， [【跳转到 18:55】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1135) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01135.jpg" width="9000"> |
| 要跳过前面七个头，用 head_idx（刚才算的是 7），7×16 相当于把前七个头跳过去。最后 head offset 做一个 0~15 的指针拓展， [【跳转到 19:20】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1160) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01160.jpg" width="9000"> |
| 指针就对齐了。然后把刚才取出来的 K、V 值 [【跳转到 19:43】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1183) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01183.jpg" width="9000"> |
| 存进 k_cache 和 v_cache 就可以了。取出来的 K、V 值，cache offset 就是具体要存放的位置，把值一一对应上。KV cache 这一部分其实要简单很多。 [【跳转到 19:48】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1188) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01188.jpg" width="9000"> |
| QKV cache 这一部分就讲完了。 [【跳转到 20:06】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1206) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01206.jpg" width="9000"> |
| （此区间无字幕） [【跳转到 20:11】](https://www.bilibili.com/video/BV1SR7k67Ee9/?t=1211) | <img src="img/第11讲_KV Cache存储过程&Triton实现/01211.jpg" width="9000"> |