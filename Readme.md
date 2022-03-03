# 饥荒mod上传工具

### 0.为什么要写这个工具

饥荒自带的ModUploader上传工具并不支持自定义排除，导致很多情况下需要手动拷贝到另外的文件夹再上传到工坊，另外网上也没有关于如何在命令行中调用这个工具的说明（命令行下有一个`--advanced`启动参数，但是并没有看到这个参数有任何效果），无法一键快速部署

### 1.如何安装本工具

安装python运行环境（version>3.8），完整下载本工程，在下载目录进入命令行输入`pip install -r requirements.txt`并运行

### 2.如何使用

- 将此工程目录下的`.uploader-config.json`配置文件拷贝至mod根目录，配置文件说明如下

  ```json5
  {
    "publishedFileId": 0,						// 工坊id，新建请置0
    "update_titles": false,					// 本次更新标题
    "update_description": false,				// 本次更新简介
    "update_previewFile": false,				// 本次更新预览图片
    "update_visibility": true,				// 本次更新mod可见性
    "title": "test",							// MOD标题
    "description": "xxxxx",					// MOD简介
    "previewFile": "path/to/your/preview",	// 工坊搜索结果中的mod预览图片
    "tags": [],								// 工坊的标签筛选，详见tags可选值
    "visibility": 2,							// Mod可见性，详见visibility可选值
    "exclude": [								// 排除文件列表，采用gitignore语法
        ".git/",
        ".uploader-config.json",
        "release/"
    ],
    "git_exclude": false,						// 导入.gitignore文件中的排除配置
    "change_note": ""							// 本次更新说明
    "tags可选值": [							  // 与在官方ModUploader中配置效果相同
        "character",
        "item",
        "pet",
        "creature",
        "environment",
        "interface",
        "utility",
        "art",
        "worldgen",
        "tweak",
        "scenario",
        "language",
        "other",
        "tutorial",
        "server_admin"
    ],
    "visibility可选值": [
        "PUBLIC              = 0",
        "FRIENDS_ONLY        = 1",
        "PRIVATE             = 2"
    ]
  }
  ```

  配置项`update_titles`、 `update_description`、 `update_previewFile`、 `update_visibility`均为单次生效，上传成功后将自动置为false，`change_note`在上传成功后会自动置空，`tags可选值`与`visibility可选值`仅起提示作用，删除不影响工具功能。

- 启动命令行窗口

  上传：
  
  ```shell
  python "本工具安装路径\moduploader.py" upload "mod路径"
  ```
  
  查看排除后具体上传文件，具体上传文件将会在`MOD路径/release`目录下：
  
  ```shell
  python "本工具安装路径\moduploader.py" build "mod路径"
  ```

### 3.已知问题

- 若modinfo版本号未修改即上传，工具不会提醒或报错，但工坊实际并不会更新
- 暂时只支持64位windows系统
- 在工坊页面中手动修改设置项不会被同步到`.uploader-config.json`的配置中，可能会造成相互覆盖
- 由于借用了官方ModUploader的appid，无法与官方ModUploader同时运行

这些问题可能会在未来版本中修复
