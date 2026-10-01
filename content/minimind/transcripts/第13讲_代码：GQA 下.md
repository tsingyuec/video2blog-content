# 代码：GQA 下 原始文稿（图-字幕分栏）

| 字幕文本 | 画面 |
| :--- | ---: |
| 好，我们这一趴继续是对 Q 和 V 的讲解。在上一趴我们其实用到了 residual 残差网络嘛，那么这一趴我们把残差网络的知识补充一下。首先，假设某个完整的函数就是完美拟合的话，它会是 H(x)=x。如果说你没有残差网络，那么 H(x)=F(x)，它就需要费力地去拟合这个 x 的值。 [【跳转到 00:00】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=0) | <img src="img/第13讲_代码：GQA 下/00000.jpg" width="9000"> |
| 但如果有残差网络的话，你在 F(x) 后面自动加上一个 x，那么它需要拟合的时候，只需要让 F(x)=0 就行。也就是说，只需要加上一个原始状态，就能在拟合上带来一些好处。这个是我们一种理解方式，就是残差网络把它初始的状态在处理完之后再加上去。那么我们简单理解 [【跳转到 00:25】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=25) | <img src="img/第13讲_代码：GQA 下/00025.jpg" width="9000"> |
| 就是说它在拟合函数上会有一些好处，能够让 F(x) 拟合得不那么麻烦。而在梯度上，残差也会有一个好处。像我们前面计算梯度的时候，因为神经网络是一层一层的，你下一层的输出就是上一层的输入，所以我们在计算梯度的时候会有 dL/dx 这个形式。 [【跳转到 00:50】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=50) | <img src="img/第13讲_代码：GQA 下/00050.jpg" width="9000"> |
| 那这个我们往后推算 dL/dH，用链式法则去推算的话，那么 dH/dx 再把这个代入，它其实就是 dF/dx 加一。那这个好处是什么呢？像我们如果出现梯度消失的问题，会导致后面的梯度计算为零，对吧？而这个加一，它就能很好地避免梯度消失的问题。 [【跳转到 01:15】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=75) | <img src="img/第13讲_代码：GQA 下/00075.jpg" width="9000"> |
| 因为你最低也是一嘛，所以它就能有效缓解梯度消失的问题。这就是在梯度上的好处，以及在拟合上的好处。这个 ResNet 也是大道至简的一个发明，但是它确实非常非常好用。 [【跳转到 01:40】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=100) | <img src="img/第13讲_代码：GQA 下/00100.jpg" width="9000"> |
| 那么我们接下来正式开始 attention 的 [【跳转到 01:55】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=115) | <img src="img/第13讲_代码：GQA 下/00115.jpg" width="9000"> |
| forward 的编写。那么 forward 方法呢，我们首先来看一下应该怎样去写。首先我们第一个步骤是进行投影，在 Linear 层里计算出 Q/K/V。然后我们投影完之后，需要去 [【跳转到 02:00】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=120) | <img src="img/第13讲_代码：GQA 下/00120.jpg" width="9000"> |
| 把输入拆分成多个头，这一步呢我们用 view 来实现。然后对于 Q 和 K 使用 RoPE，对于 K 和 V 使用 repeat。然后这一步呢，我们需要去注意 KV cache。 [【跳转到 02:25】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=145) | <img src="img/第13讲_代码：GQA 下/00145.jpg" width="9000"> |
| 也就是 KV 需要有一个缓存。这个缓存的意义呢，就是说像我们在每次计算一个值之前， [【跳转到 02:50】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=170) | <img src="img/第13讲_代码：GQA 下/00170.jpg" width="9000"> |
| 比如说我们计算这个值之前，是需要用到前面的 K 和 V，对吧？那么我们需要计算下一个值的话，让它重新计算前面的 K 和 V 就太浪费了。我们把这一部分 K 和 V 缓存起来，当下一部分要计算的时候直接拿出来用，这就是 KV cache。 [【跳转到 02:56】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=176) | <img src="img/第13讲_代码：GQA 下/00176.jpg" width="9000"> |
| 我们需要去注意有没有 KV cache，然后呢去进行 attention 的计算，就是我们那个 attention 公式嘛，就是 Q 乘以 K 的 T 次方，然后除以 d，最后再乘一个 V，那这个就是计算。那么最后呢，最后拼接头，输出投影。 [【跳转到 03:17】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=197) | <img src="img/第13讲_代码：GQA 下/00197.jpg" width="9000"> |
| 其实就这几步。那我们现在一步一步来把这个实现。首先呢依旧是 forward，我们和 Module 都需要实现 forward 这个方法，再输入一个 torch.Tensor，然后需要用到位置编码，需要用到 rotary embedding。 [【跳转到 03:42】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=222) | <img src="img/第13讲_代码：GQA 下/00222.jpg" width="9000"> |
| 那么这个呢我们让它是一个元组形式，元组里面存放了两个 torch.Tensor，也就是我们前面计算的 cos 和 sin。我们在前面这个类里把这个给导入进去。好，然后呢我们需要用到 past_key_value。 [【跳转到 04:07】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=247) | <img src="img/第13讲_代码：GQA 下/00247.jpg" width="9000"> |
| 这个 past_key 和 value 呢，就是我们先前的缓存下来的 key 和 value。我们它是一个 Optional 类型，可空的，因为第一个的话它也是没有的，后面的话是有的，所以用 Optional。然后依旧是一个 key 和 value 嘛，两个 tensor。然后呢就是我们的是否要 use_cache，我们要加上 use_cache，是否要用到 [【跳转到 04:32】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=272) | <img src="img/第13讲_代码：GQA 下/00272.jpg" width="9000"> |
| 我们让它默认等于 False。然后呢就是 attention_mask，我们的 attention mask 呢依旧是 Optional，然后是一个 torch.Tensor，哦等等，默认值等于 None。好，那我们接下来呢就是实现我们最简单的 [【跳转到 04:57】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=297) | <img src="img/第13讲_代码：GQA 下/00297.jpg" width="9000"> |
| 一步一步来。首先我们需要去算出我们的 Q/K/V 嘛，那么前面我们的投影其实是已经算过了。我们先把我们需要用到的向量里的 shape 里的每个维度给拆一下，x.shape 我们把它拆一下。 [【跳转到 05:22】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=322) | <img src="img/第13讲_代码：GQA 下/00322.jpg" width="9000"> |
| 拆完之后呢，对于 Q/K/V，我们用到前面的 Q/K/V，等于用到我们前面的投影计算出来之后，我们对 Q/K/V 进行一个拆分，把它拆分成多个头。现在呢它们每个其实都是 512 个维度，我们把它拆分成八个头，每个头是 64 个维度，就用到这个，在前面我们定义的嘛，512 [【跳转到 05:47】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=347) | <img src="img/第13讲_代码：GQA 下/00347.jpg" width="9000"> |
| 然后我们用八个头，那么每个头拆分就是 64 个维度。拆分完之后，对于 Q 和 K 我们使用 RoPE 来进行一个位置编码，我们调用一下位置编码函数，然后 xq、xk 就我们前面的应用位置编码的函数 (xq, xk)。 [【跳转到 06:12】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=372) | <img src="img/第13讲_代码：GQA 下/00372.jpg" width="9000"> |
| 然后用上把序列长度之前的，就让它序列长度正好相等，然后我们应用上，把这个 Q 和 K 融入我们的位置信息。然后对于 K 和 V 呢，我们再进行相关的处理。首先如果说有我们前面的 K 和 V，就是我刚刚举的例子，我们前面的 K 和 V 和 past 传过来的， [【跳转到 06:37】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=397) | <img src="img/第13讲_代码：GQA 下/00397.jpg" width="9000"> |
| 如果不为 None 的话，我们就要把前面的 K 和 V 和现在的 K 和 V 进行一个拼接，cat。然后我们把 past_k 和 V 的第一个，取第一个，也就是取出 K，然后和现在的 K 拼接，然后 [1] 取出 V。 [【跳转到 07:02】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=422) | <img src="img/第13讲_代码：GQA 下/00422.jpg" width="9000"> |
| 然后 V 呢我们也是我们取出之后进行拼接，然后我们把现在的这个作为下一次的 past_key_value，等于 (xk, xv)。也就是说，我们把上一个的拼接过来之后，拼接完之后使用之后，我们再把它放到下一个的 past_kv 里，用作下一次的拼接。然后对于 Q/K/V [【跳转到 07:27】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=447) | <img src="img/第13讲_代码：GQA 下/00447.jpg" width="9000"> |
| 我们去进行一个转化，xq 我们需要用到 transpose，我们需要去把它进行一个维度交换。那么这个维度交换呢，是因为我们后续计算的时候需要去让它和 K 和 V 进行计算了。 [【跳转到 07:52】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=472) | <img src="img/第13讲_代码：GQA 下/00472.jpg" width="9000"> |
| 呃现在它应该是四个维度，分别是 batch_size、num_heads，然后 seq_len 和 head_dim，它原本是 seq_len，然后这里是头在第三个位置，head_dim 在第四个位置。而在 PyTorch 里计算的话， [【跳转到 08:17】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=497) | <img src="img/第13讲_代码：GQA 下/00497.jpg" width="9000"> |
| 他会把前面两个认为是批次，后面两个认为是计算，应该是这样。我们要计算的是序列每个长序列里的每个头，来找一下 [【跳转到 08:42】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=522) | <img src="img/第13讲_代码：GQA 下/00522.jpg" width="9000"> |
| 找一下我的那张图，他所需要计算的是这么多个序列里的每个维度。 [【跳转到 08:54】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=534) | <img src="img/第13讲_代码：GQA 下/00534.jpg" width="9000"> |
| （此区间无字幕） [【跳转到 08:59】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=539) | <img src="img/第13讲_代码：GQA 下/00539.jpg" width="9000"> |
| 需要去跟他计算，而不是说它每个头计算，所以我们需要去交换一下。 [【跳转到 09:04】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=544) | <img src="img/第13讲_代码：GQA 下/00544.jpg" width="9000"> |
| 把头放在前面，这部分不清楚的话大家可以再问一下 AI。 [【跳转到 09:09】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=549) | <img src="img/第13讲_代码：GQA 下/00549.jpg" width="9000"> |
| 然后接下来呢，我们 Q/K/V 处理好之后，就是进行我们最基本的这个 attention 计算。首先呢我们先检查一下就是能不能使用 FlashAttention，如果能使用 FlashAttention 并且满足相应条件、attention_mask [【跳转到 09:14】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=554) | <img src="img/第13讲_代码：GQA 下/00554.jpg" width="9000"> |
| is None 或者它等于一，就让 mask 等于 None。如果说是这样的话，我们让 attention_mask，我们让它的掩码等于一个 None， [【跳转到 09:39】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=579) | <img src="img/第13讲_代码：GQA 下/00579.jpg" width="9000"> |
| if 这个 attention_mask 等到什么，如果不是 None 的话，我们就让 attention_mask 我们把它进行一个转换，把它转成一和负 inf 的形式， [【跳转到 10:04】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=604) | <img src="img/第13讲_代码：GQA 下/00604.jpg" width="9000"> |
| 让它变成一个 (batch_size, 1, 1, seq_len) 的形状，然后一。对，所以这个掩码的话会比较复杂一些，大家看一下就好。 [【跳转到 10:29】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=629) | <img src="img/第13讲_代码：GQA 下/00629.jpg" width="9000"> |
| 然后就是 torch 这里，因为我们用 FlashAttention 嘛，我们就需要去用到它内置的一个函数。这里呢需要导入一个包，叫 import torch.nn.functional，也就是它内置的一些函数，我们把它导为 F。 [【跳转到 10:54】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=654) | <img src="img/第13讲_代码：GQA 下/00654.jpg" width="9000"> |
| 用它内置的计算的话，就是这个 scaled_dot_product_attention 来计算，这个是因为它内置，而且用 FlashAttention 比较高效。我们把它所需要的参数都输入进去：attention_mask，然后 dropout 的 self.dropout，if self.training [【跳转到 11:19】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=679) | <img src="img/第13讲_代码：GQA 下/00679.jpg" width="9000"> |
| 如果它是 training 的话就用 dropout，如果它不是 training，是推理的话，我们就用 0.0。然后 is_causal 设为 True，看一下有什么报错吗。 [【跳转到 11:44】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=704) | <img src="img/第13讲_代码：GQA 下/00704.jpg" width="9000"> |
| 好，if……好。那么这里我们就编写好了。这个 self.training 呢，就是我们 PyTorch 的时候是启用训练模式还是推理模式。这个呢就是这样，不了解的可以自己去再查一查。然后我们自己再来实现一个，我们不用它内置的函数的话，我们自己该怎么实现呢？我们自己编写一下。 [【跳转到 12:09】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=729) | <img src="img/第13讲_代码：GQA 下/00729.jpg" width="9000"> |
| 首先我们就用它最基础的公式来写就行。我们让 Q 去和这个 K 的转置去进行相乘，transpose 2,1，我们是让它和它的转置进行一个相乘，相乘之后再除以它维度的一个开方嘛。然后呢我们需要去应用掩码。 [【跳转到 12:34】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=754) | <img src="img/第13讲_代码：GQA 下/00754.jpg" width="9000"> |
| 应用掩码的话，就是需要去让这个我们现在计算出的 [【跳转到 12:59】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=779) | <img src="img/第13讲_代码：GQA 下/00779.jpg" width="9000"> |
| 这个 scores，加上我们用 torch.triu 生成的掩码， [【跳转到 13:04】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=784) | <img src="img/第13讲_代码：GQA 下/00784.jpg" width="9000"> |
| 就这个三角形，然后 torch.full，我们让三角形的上半部分，也就是这个我们当前词后面的部分，都把它填满 float 负 inf， [【跳转到 13:09】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=789) | <img src="img/第13讲_代码：GQA 下/00789.jpg" width="9000"> |
| 也就是负无穷大，它在经过 softmax 之后它会转化成零。不懂的可以去看一下 3Blue1Brown 的视频。然后这里之后我们去让 diagonal 等于一，因为是从对角线往后遮蔽嘛。 [【跳转到 13:34】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=814) | <img src="img/第13讲_代码：GQA 下/00814.jpg" width="9000"> |
| 我们让它是这样计算，计算完之后，把这个 scores [【跳转到 13:54】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=834) | <img src="img/第13讲_代码：GQA 下/00834.jpg" width="9000"> |
| 在第一个维度上进行一些扩展，scores，咳，这个呢就是实现了这样的一个计算嘛。 [【跳转到 13:59】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=839) | <img src="img/第13讲_代码：GQA 下/00839.jpg" width="9000"> |
| 然后 [【跳转到 14:21】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=861) | <img src="img/第13讲_代码：GQA 下/00861.jpg" width="9000"> |
| 嘶，下面还有就是过 attention 的 mask，mask is not None 的话，这里就是一些扩展的 attention mask，这一部分我直接把它写上来。那么这个掩码应用完之后， [【跳转到 14:26】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=866) | <img src="img/第13讲_代码：GQA 下/00866.jpg" width="9000"> |
| 我们去进行后续的 softmax 层的应用。softmax 层应用我们继续用 F 里面自带的这样一个 softmax 函数来对 scores 进行一个概率化的处理，依旧是用 float 来让它变成 float [【跳转到 14:51】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=891) | <img src="img/第13讲_代码：GQA 下/00891.jpg" width="9000"> |
| 32，训练才更稳定。因为我们用了 float32，所以我们再把它转化过来，转化为原本的类型。然后应用完 softmax 之后呢，我们再进行一次，进行一层 dropout。那么这里呢是我感觉就是原架构图上 [【跳转到 15:16】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=916) | <img src="img/第13讲_代码：GQA 下/00916.jpg" width="9000"> |
| 他并没有体现的一部分，就是他代码里写了 dropout 的，但是他这里自己没有写。 [【跳转到 15:41】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=941) | <img src="img/第13讲_代码：GQA 下/00941.jpg" width="9000"> |
| 那我们现在就是相当于把这 softmax [【跳转到 15:46】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=946) | <img src="img/第13讲_代码：GQA 下/00946.jpg" width="9000"> |
| 这一步就完成了吗？softmax 完成了之后， [【跳转到 15:51】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=951) | <img src="img/第13讲_代码：GQA 下/00951.jpg" width="9000"> |
| 我们去让我们这个 output，在这一步我们让它和这里的 V 相乘。 [【跳转到 15:56】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=956) | <img src="img/第13讲_代码：GQA 下/00956.jpg" width="9000"> |
| output 等于 scores 和 V 的矩阵进行一个点乘。 [【跳转到 16:03】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=963) | <img src="img/第13讲_代码：GQA 下/00963.jpg" width="9000"> |
| 然后最后我们对 output 这个向量，啊这里是应该是放在 else 里面的，我们对这个 output 进行一个继续的处理，output 等于 output 点 transpose。呃因为我们一开始把一和二交换了嘛，我们让 seq_len 变成了第 3 号位。 [【跳转到 16:08】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=968) | <img src="img/第13讲_代码：GQA 下/00968.jpg" width="9000"> |
| 我们这里再把它交换回来，然后再 reshape 变成 (b, s, seq_len) 然后一。我们在这里把 output 再进行一个维度的变化，它现在的维度呢 [【跳转到 16:33】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=993) | <img src="img/第13讲_代码：GQA 下/00993.jpg" width="9000"> |
| 它现在的维度呢，就变回了，咳，变成了一个这样的形这样的情况。然后我们交换之后，我们把 seq_len 又放回了这里，然后再进行一个 reshape，然后呢因为我们需要用到残差嘛，我需要把最前面、就它一开始的那个部分给加上来。 [【跳转到 16:58】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1018) | <img src="img/第13讲_代码：GQA 下/01018.jpg" width="9000"> |
| 我们用到残差。 [【跳转到 17:23】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1043) | <img src="img/第13讲_代码：GQA 下/01043.jpg" width="9000"> |
| 在这里我们应用上了。然后之后呢，我们把 output 和我们前面计算的 past_kv 给传回去。 [【跳转到 17:30】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1050) | <img src="img/第13讲_代码：GQA 下/01050.jpg" width="9000"> |
| 这样呢，整个 forward 的最复杂的、最核心的内容我们就已经算完了。其实最核心的内容呢，就是首先呢我们把 Q/K/V，我们把 x 投影，我们把 Q/K/V 用前面的投影计算之后拆分成多个头。 [【跳转到 17:35】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1055) | <img src="img/第13讲_代码：GQA 下/01055.jpg" width="9000"> |
| 我们这里是拆分成八个头，不过只有对 Q 和 K 使用 RoPE 进行位置编码。 [【跳转到 18:00】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1080) | <img src="img/第13讲_代码：GQA 下/01080.jpg" width="9000"> |
| 然后对 K 和 V 呢，如果有 KV cache 的话，我们添加上原来的、过去的 KV。 [【跳转到 18:07】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1087) | <img src="img/第13讲_代码：GQA 下/01087.jpg" width="9000"> |
| 然后进行一个复制，进行一个 repeat 的复制。复制完之后，我们进行最核心的 attention 的计算。对于 Q 和 K 呢， [【跳转到 18:13】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1093) | <img src="img/第13讲_代码：GQA 下/01093.jpg" width="9000"> |
| 我们在这里进行一个点积计算，这个呢是它内置的实现。 [【跳转到 18:21】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1101) | <img src="img/第13讲_代码：GQA 下/01101.jpg" width="9000"> |
| 这里是我们自己的实现，对 Q 和 K 进行一个计算之后再除以一个它的维度的开方，然后在这里呢我们是相当于是应用了我们这里的掩码。 [【跳转到 18:26】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1106) | <img src="img/第13讲_代码：GQA 下/01106.jpg" width="9000"> |
| 应用完掩码之后，在这里应用它内部的 softmax 函数，然后在这里进行 dropout。 [【跳转到 18:36】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1116) | <img src="img/第13讲_代码：GQA 下/01116.jpg" width="9000"> |
| 这里呢是上面没写的，我们应用 dropout 之后再和 V 这里相乘。 [【跳转到 18:41】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1121) | <img src="img/第13讲_代码：GQA 下/01121.jpg" width="9000"> |
| 相乘完之后，在这个 linear 层我们需要把头给拼回来。 [【跳转到 18:47】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1127) | <img src="img/第13讲_代码：GQA 下/01127.jpg" width="9000"> |
| 因为我们前面是拆分成了八个头，这里我们需要把八个头拼起来，再变成 512、512 维，然后应用残差之后再把它输出。 [【跳转到 18:52】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1132) | <img src="img/第13讲_代码：GQA 下/01132.jpg" width="9000"> |
| 这就是我们最核心的 GQA 的实现。 [【跳转到 19:00】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1140) | <img src="img/第13讲_代码：GQA 下/01140.jpg" width="9000"> |
| 还有不懂的地方大家可以看一下我的 Notion 笔记，对照这个图理解一下，或者说问一下 AI 都可以。好，那么我们这一 part 讲解完毕，我们下一块呢进入 FFN 的讲解。 [【跳转到 19:05】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1145) | <img src="img/第13讲_代码：GQA 下/01145.jpg" width="9000"> |
| 下一块就比较简单了。 [【跳转到 19:16】](https://www.bilibili.com/video/BV1T2k6BaEeC/?p=13&t=1156) | <img src="img/第13讲_代码：GQA 下/01156.jpg" width="9000"> |