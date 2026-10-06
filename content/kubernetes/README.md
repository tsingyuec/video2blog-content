# 系列：Kubernetes RBAC 权限控制

- **平台**：YouTube
- **作者**：Anton Putra
- **来源**：[Kubernetes RBAC Explained](https://www.youtube.com/watch?v=iE9Qb8dHqWI)
- **视频数**：1（约 23 分钟）
- **主题**：从「如何从零设计一个授权系统」讲起，一步步推导出 Kubernetes RBAC 的三要素——身份（User / ServiceAccount / Group）、角色（Role / ClusterRole）、绑定（RoleBinding / ClusterRoleBinding），并用 Minikube 动手验证命名空间边界、跨命名空间绑定与集群范围授权。

## 视频索引

| 视频键 | 标题 | 时长 | 博客 | 原视频 |
| --- | --- | ---: | --- | --- |
| iE9Qb8dHqWI | Kubernetes RBAC 权限控制详解 | 23:17 | [博客](blog/Kubernetes%20RBAC%20权限控制详解.md) | [YouTube](https://www.youtube.com/watch?v=iE9Qb8dHqWI) |

## 内容速览

- 一、请求打到 apiserver 之后：认证（401）→ 授权（403）→ 准入控制
- 二、从零设计授权系统：为什么需要「角色」
- 三、Kubernetes 三要素：身份、角色、绑定
- 四、身份：用户（证书 CN）、ServiceAccount、组
- 五、权限：资源 / API 端点 / 动词，rule 与 Role
- 六、绑定：RoleBinding 的 roleRef 与 subjects
- 七、动手实践：用 impersonation 验证 QA 只读 staging
- 八、Role 与 ClusterRole：命名空间 vs 集群范围
- 九、混用 RoleBinding 与 ClusterRole 的三个边角场景
- 十、用组合格式精简 rules

## 核心结论

- RBAC 的本质是**把用户与权限解耦**，中间用「角色」承接、用「绑定」连接。
- **Role/RoleBinding 只在命名空间内生效**；集群范围资源（PersistentVolume、Node）必须用 **ClusterRole/ClusterRoleBinding**。
- **RoleBinding + ClusterRole** 只授予 RoleBinding 所在命名空间的权限；**ClusterRoleBinding + ClusterRole** 作用于全集群，且不能引用 Role。

> 说明：本系列中间结果（视频、抽帧、字幕、图文稿）位于 `_work/kubernetes/`；`content/kubernetes/` 只收录博客与配图。
