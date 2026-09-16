# MOSAIC project website

独立静态项目主页，无需 npm、构建或第三方 CDN。页面正文为英文，依次包含封面、交互式方法总览、Pipeline、效率对比、VR 后处理、Text-to-Scene、Image-to-Scene、连续编辑、Demo 和 Citation。

## 本地预览

在当前目录运行以下命令以预览完整网站（3D 模块需要通过 HTTP 加载）：

```bash
python3 -m http.server 8000
```

访问 http://localhost:8000 。直接双击 `index.html` 可查看静态内容和图片对比，但浏览器的本地文件限制会阻止 3D 模块加载。将整个仓库上传到静态托管服务即可部署；所有资源均使用相对路径，支持子目录托管，不需要原始素材目录或 Blender。

## 内容与素材

- `index.html`：项目文案、模块内容、示例 prompt、资源链接和 BibTeX。
- `styles.css`：桌面及手机布局；`.hero-background` 控制 teaser 背景透明度。
- `script.js`：手机导航、当前模块高亮、四阶段切换、引用复制。
- `editing.js`：四场景、三编辑方式及前后对比拖拽；`editScenes` 存放场景标识和指令。
- `assets/edits/`：24 张连续编辑原图的独立副本，保留原始 PNG 画质。
- `scene-viewer.js`：真实 3D 场景、自动旋转、暂停/恢复、重置视角及阶段切换。
- `result-scenes.js`：Text / Image 生成结果的自动旋转与独立暂停/恢复按钮；结果场景不响应拖拽、平移或缩放。
- `assets/scenes/`：四阶段完整场景 GLB（内嵌贴图）、透明背景预览图和导出统计。
- `assets/results/`：Text / Image 生成结果 GLB、三张 Image 输入原图及导出统计；全部资源独立打包，不读取电脑绝对路径。
- `assets/media/`：网页优化后的 Demo 视频及封面、Pipeline 图和 VR 后处理图。
- `vendor/model-viewer/`：本地打包的 model-viewer 4.3.1，包含上游许可证；运行时无需 CDN。
- `assets/teaser.jpg`：来自项目 `docs/imgs/teaser.jpg` 的独立副本。
- `assets/favicon.svg`：简单的拼块图标。

Demo、Pipeline、VR 后处理、Text-to-Scene 和 Image-to-Scene 均已接入完整素材。Text-to-Scene 当前包含 5 个真实 3D 结果，以两列排列并按 Atmosphere、Detailed、Functional 命名；Image-to-Scene 包含 3 行真实对比，每行左侧为输入原图、右侧为对应 3D 场景。连续编辑模块已接入完整图片，Overview 3D 模块已接入用户提供的 Blender 场景。

效率模块仅比较端到端总时间：Text 输入为 MOSAIC 4:55、Codex 13:50、SceneSmith 83:54；Image 输入为 MOSAIC 7:57、Codex 14:16，SceneSmith 未报告。页面不展示 Layout 与 Asset 的分项时间。

替换内容时：

1. Demo：替换 `assets/media/demo.mp4` 和 `assets/media/demo-poster.jpg`。
2. Text-to-Scene：替换 `assets/results/text-*.glb`，并同步更新 `index.html` 中的标题与 prompt。
3. Image-to-Scene：成对替换 `assets/results/image-*.glb` 和 `assets/results/image-*-source.png`。
4. Pipeline 与后处理：替换 `assets/media/pipeline.png` 和 `assets/media/post.png`。
5. 3D 场景：替换 `assets/scenes/livingroom-{stage}.glb` 和预览图；调整 `scene-viewer.js` 及 `index.html` 中的默认相机视角。
6. 作者与论文：在封面预留注释处填写确认的作者及机构，按需添加论文按钮；用正式 BibTeX 替换 `#bibtex`，同时移除草稿说明。

## 连续编辑素材

`#editing` 一次展示一个场景：桌面左侧选场景，上方选 Sketch / BBox / Language Edit。手机场景选择调整为两列。比较图左侧为编辑前，右侧为编辑后，支持鼠标、触摸及方向键，Home / End 可查看完整编辑后 / 编辑前。切换场景或方式保留另一项选择，分界线重置为 50%。

已接入用户提供的 24 张完整场景图片，全部复制到网站内的 `assets/edits/`，不使用软链接、电脑绝对路径或网站目录外的图片。将整个仓库复制到其他电脑或上传到静态托管服务即可独立显示，无需原始 `edit` 目录。

图片按场景和编辑方式独立配对，命名规则如下：

```text
assets/edits/{scene}_{method}_input.png   # 左侧，编辑前
assets/edits/{scene}_{method}_output.png  # 右侧，编辑后

scene:  bedroom / livingroom / study / studio
method: sketch / bbox / language
```

对应场景为 Warm bedroom、Living room、Study、Music studio。Sketch / BBox 使用各自带交互标记的 input，不将上一步的 output 代替下一步的 input。Language Edit 直接使用已提供的完整场景结果，无需额外合成示意小图。

所有图片均为 4:3，原始分辨率为 2048×1536 或 1448×1086；比较器按同一画幅等比显示完整图片，不会随滑块拖动缩放。每次仅加载当前选中的一对图片，快速切换时忽略旧请求，避免串图。替换素材时沿用相同命名，并保持成对图片的相机视角和画幅一致。

## 交互式方法总览

封面后保留四阶段交互场景。在其上方以三个独立圆角文字卡片介绍：多模态生成与编辑（Language / Image / Sketch / BBox）；高效生成（层次化规划、Layout 与 Asset 解耦并行、无需渲染反馈）；VR 操作友好（碰撞处理、悬浮修正、依赖传播、旋转对齐）。重点术语显示为说明文字下方的胶囊标签；手机端卡片纵向排列。

查看器使用原有四阶段完整资产场景，支持旋转、缩放和平移；已移除 Layout 示意切换、层次列表、流程文字和重复的效率数字，完整效率比较仍在 `#efficiency`。

Pipeline、Efficiency 和 Post-processing 紧随 Overview，分别作为第 2、3、4 个内容模块。

## Text / Image 生成结果

Text-to-Scene 每行展示两个结果，按目录前缀排序：Atmosphere、Detailed、Functional。Image-to-Scene 共三行，分别为 Bedroom、Living room、Meeting room，每行左侧展示 1254×1254 输入原图，右侧展示对应 3D 场景。

所有结果场景默认缓慢旋转，各自提供 Pause / Resume rotation 按钮；不提供拖拽、平移、缩放或层次切换。系统开启“减少动态效果”时默认停止旋转。为便于观察室内，网页导出统一移除顶面和一侧墙，并将贴图嵌入 GLB。当前单个文件约 8–21 MB，均低于 GitHub 单文件限制。

源文件来自网站仓库同级的 `scene/text/` 和 `scene/img/`。重新导出命令如下，脚本不会覆盖源 `.blend`：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python tools/export_result_scenes.py
```

`scene/text/atmosphere_livingroom/` 当前只有 `input.txt`，没有 `.blend`，因此该类别尚未显示；其余 5 个 Text 场景和 3 个 Image 场景已完整接入。

## 3D 场景展示

源场景来自原 MOSAIC 开发目录中的 `scene/detailed_livingroom_retry8.blend`。源文件和美化后的 Blender 副本未放入这个独立网站仓库。

展示处理：原场景南侧已开放，再移除西侧墙、顶面和对应悬空墙饰，保留两面相邻背景墙；调整为暖色石膏墙面，保留木地板及家具贴图，增加薄底座和柔和环境光，烘焙完整场景的地面接触阴影，并清理电视屏幕的噪点纹理。家具网格和贴图已针对网页缩减，具体大小见 `assets/scenes/scene-info.json`。GLB 内嵌所需贴图，不引用源机器路径。

默认展示完整 Supported 场景，每秒旋转 5°。左键拖动旋转，滚轮缩放，右键拖动平移；触摸设备支持单指旋转及双指缩放/平移。操作后等待 3 秒恢复自动旋转，可手动暂停或重置。系统开启“减少动态效果”时默认暂停自动旋转。

四个选项展示按源文件物体类别整理的累计层次，属于此静态场景的展示分组，不是对后端生成过程的录制回放：

- Structure：地板、两面保留的墙和底座。
- Attached：增加保留的墙饰与顶灯。
- Primary：增加独立家具、落地灯和大型物体。
- Supported：增加桌面餐具、杯子、书、台面植物和电视。

如本机仍保留原 MOSAIC 开发目录，可通过 Blender 重建网页资源（命令从本仓库根目录运行）：

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python tools/export_livingroom.py
```

此脚本依赖原 MOSAIC 开发目录中的源 `.blend`，只用于重新导出网页资源。部署后的浏览器不依赖它。查看器使用 [model-viewer](https://modelviewer.dev/)，其光照与交互参数参见[官方示例](https://modelviewer.dev/examples/lighting-and-environment.html)。

Pipeline 使用 `pipeline.pdf` 渲染的网页图，VR 后处理使用 `post.pdf` 渲染的网页图；部署不依赖仓库外的 PDF。Pipeline 文案依据原 MOSAIC 仓库中的 `docs/architecture.md`、`docs/visionpro_staged_scene_delivery.md` 及项目实现整理。页面结构参考 [SceneSmith](https://scenesmith.github.io/)，页面代码为本项目新写。
