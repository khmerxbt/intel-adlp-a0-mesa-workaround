# QY0Z / Alder Lake A0 核显 Mesa 临时修复

这是针对 **ADL GT2、revision 0 工程样品** 的实验性 Mesa 用户态补丁。
目前只在一台 **QY0Z / i7-12700H ES、8086:46a1 rev 00** 上验证。
**不是通用 ES 驱动，也不是 i915 内核驱动或 BIOS 修复。QXSG 尚未实测。**

核心思路是恢复上游删除的 `Wa_22011186057`，禁止受影响硬件使用
CCS 图像/表面压缩，并补充 Iris 和 ISL modifier 检查。
这里的 CCS 压缩与内核 CCS 计算引擎不是一回事。

可先对单个程序尝试上游已有的诊断选项：

```sh
INTEL_DEBUG=noccs your-application
```

参考机器上，补丁和该选项分别通过了真实 Intel GPU 的像素、shader 检查。
另有深度、模板、纹理、4× MSAA 测试；原生 OpenGL/Vulkan 及 Steam 64/32 位
测试通过。PCSX2《战神 II》开场同一场景 1×/2× 约 60 FPS，3× 约 50 FPS，
这些是抽样计数，不代表全流程平均帧率。

没有在同一次启动中进行默认开启压缩的完整 A/B 对照，不能断言所有历史
死机只有一个原因。GuC/DMC 等原有警告仍在；长时间稳定性、其他 ES 型号、
Jellyfin/iHD 视频编解码、OpenCL 和虚拟机 GPU 加速均未完成验证。

先阅读 [研究记录及中文社区来源](research.md)、[验证范围](validation.md)、
[构建说明](build.md) 和 [部署/回滚](integration.md)。不要直接把 Ubuntu 的
二进制复制到 Debian，也不要在 Xorg 中混用不同版本的 Mesa 组件。
本仓库提供源码、构建配方及验证工具，不含 BIOS、游戏 ISO、存档或预编译驱动。
