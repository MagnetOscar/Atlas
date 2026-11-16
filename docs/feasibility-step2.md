# 第二步 汇率读取与回程组件可行性

2026 年 11 月 16 日。本轮基于个人 Fork 提交 `115e1a1cbecf946c0b6f8970a10dc5f90ff6a6b2`，只做一次性验证和源码、许可证审计，不部署功能。用户本轮将汇率计划明确为每天 **UTC 00:00** 获取一次，不需要短周期历史。

## 结论

| 项目 | 结果 | 尚待处理 |
| --- | --- | --- |
| CA 直接读取 Google Finance 当前汇率 | 通过；USD/CNY、EUR/CNY、JPY/CNY 均提取到各自主报价和 UTC 时间 | 网页结构与浏览器兼容性依赖；不是稳定官方 API |
| 每日 UTC 00:00 获取一次 | 调度方案可实现，未安装定时器 | 仍须实际部署、跨日及断网验证，不能把计划当运行结果 |
| 现成三网回程组件 | 存在；Transit 有发布资产，Enhanced 自带相应伴生组件 | 当前系统兼容性、采集权限、ASN 来源、国内目标及生产闭环未验收 |
| 同一项目整合多个来源 | 可在现有 Fork 中集成，无需创建第二个 Fork | 按实际复用文件核实并保留每项许可及来源 |

## Google Finance 读取实测

使用本仓库的 [一次性诊断脚本](../scripts/feasibility/read_google_fx.py)，通过已有 SSH 以普通用户在 CA 的 Python 标准库中执行，不上传远端文件、不调用 sudo、不读取账号或 Cookie、不写数据库或缓存。

实测时间：**2026-11-16 11:11:36 UTC**。三个货币对均收到 HTTP 200，最终 URL 和标题匹配请求货币对，并从主报价区域提取正数报价及页面标注的 UTC 更新时间。压缩响应大小分别约 189、203、210 KB。公开记录只保留技术结果，不复制整页 HTML、报价历史或实时行情数据。

对照结果不能省略：

- 普通诊断 User-Agent 在 Windows 和 CA 均跳转到 `finance/unsupported`；HTTP 200 不能单独算成功。
- 常规桌面浏览器 User-Agent 能返回对应货币对页面；没有使用登录会话、Cookie、验证码绕过或无头浏览器。
- 旧的 `data-last-price` 属性当前不存在。实际主报价由可见货币对标识与其 UTC 时间附近文本关联提取，不能抓页面上第一个数字，否则会误取其他资产。
- 脚本是可复验的诊断工具，不是本轮已经集成的生产模块。未来网页改版、访问限制或字段不完整时必须显式失败，不能制造汇率。

手动复验（Python 3 标准库；不会建立定时任务）：

```sh
python3 scripts/feasibility/read_google_fx.py --desktop-agent USD-CNY EUR-CNY JPY-CNY
```

`--inspect-layout` 仅用于诊断可见字段；默认只输出指定报价和技术元数据。输出包含即时行情，不应直接作为公共仓库附件。无效目的页、错配货币对、缺少主报价或时间时返回失败。

### 每天一次的计划

后续由 CA 在固定 UTC 日界获取各所需货币对，每个日期只保留最后一次成功快照及报价时间、获取时间、来源和状态；不查询分时或长期历史。顶栏的多个币种使用同一批快照换算，页面刷新不触发上游请求。

调度可使用现有 CA 框架中的 systemd timer，日历表达式为 `*-*-* 00:00:00 UTC`；北京时间为每天 08:00。主机错过执行时可以启动后补取一次并显示实际获取时间。失败则保留上次值并明确显示过期，不能默默替换为其他数据源或假定汇率为 1。

这里取得的是执行时**最新可得报价**，不是精确午夜成交价、银行结售汇价或官方收盘价；周末及数据延迟都应保留原报价时间。本轮没有安装 timer，也没有做连续多日午夜实测。

### 数据来源和公开发行边界

用户指定的 Google 搜索卡片标注 Morningstar。Google 的 [数据说明](https://www.google.com/intl/en/googlefinance/disclaimer/)同样列明货币报价来源。对应 [Google Finance 页面](https://www.google.com/finance/quote/USD-CNY?hl=en)提供报价和时间，本轮验证的是这个公开展示入口，不是直接访问 Morningstar 数据 API。

Google 页面同时对下载、缓存、处理和再分发数据作出使用限制。**技术读取通过不等于数据复用许可已经解决**；主题代码的 MIT 也不覆盖 Google/Morningstar 的行情权利。不能把这次诊断直接包装成可无条件供公众使用的行情服务。正式公开版的数据接入方式及授权仍需落实，未确认前不把 Google 抓取器作为默认启用的公共汇率后端。

## 后续确认 复用现有汇率接口与限定使用位置

用户在本轮后续说明中优先选择沿用主题已有两个 API，只让汇率用于全部服务器的首页顶栏汇总；每台服务器自己的金额使用本币。是否完全维持现有缓存机制，以它能否满足用户对日常估算或最新已公布数据的要求为条件，不能把条件性意见写成已批准不再修正缓存。

当前 `src/utils/financeHelper.ts` 的实际逻辑如下：

- 首选 `https://open.er-api.com/v6/latest/CNY`，失败或整份校验不通过才尝试 `https://api.frankfurter.app/latest?from=CNY`。
- 网络请求由浏览器组件挂载触发，结果保存在该浏览器 localStorage。缓存日期使用浏览器本地年月日；同日继续使用缓存，并非每次打开重新请求，也不是 CA 的 UTC 00:00 调度。已经打开的页面不会仅因跨日而自动刷新汇率。
- 先将节点金额按汇率转换成人民币汇总，再转换到选择的汇总币种；不是只更换币种符号。
- 手动覆盖也在浏览器本地保存。在线来源失败时先用旧缓存，再用内置静态参考表；显示的抓取时间不是上游实际行情时间。
- 节点卡片原始价格与剩余价值已使用节点本币；`InstanceDetail.vue` 的剩余价值仍按全局币种换算。后续按用户范围限制时需要纠正该位置，并审查对比、导出等工具，不能宣称现状已仅限顶栏。

接口只读复验：三个入口均 HTTP 200。首选公开接口覆盖本主题要求的 12 个非人民币币种；旧 Frankfurter 入口只返回 29 个目标币种，缺少 RUB、VND，而当前校验要求 12 个币种全部存在，因此此备用响应会被整体拒绝。Frankfurter v2 的默认聚合端点覆盖这 12 个币种，但本轮没有替换配置。

现有按日缓存可用于一般费用参考，不能保证每次使用都是上游最新一批。若要求最新已公布数据，最小调整是保留数据来源、依据来源更新元数据与缓存过期状态决定是否刷新，而不是仅按浏览器日期；具体刷新策略尚未实施。

公开接入条件也不同：现用 [ExchangeRate-API Open Access](https://www.exchangerate-api.com/docs/free)无需账号或 Key、每天更新、允许终端换算及缓存，但要求页面署名且不允许转售/再分发原始数据服务。[Frankfurter v2](https://frankfurter.dev/)无需 Key，其默认聚合数据说明允许免费商用及缓存；直接指定原始供应商时仍须核对该供应商条款。当前源码未发现 ExchangeRate-API 的页面署名链接，正式使用及发行时应补齐。无需因此把 Google 网页抓取作为默认来源。

本次后续核查只更新研究记录，没有修改接口、缓存、汇率 UI、生产服务或调度。

## 回程组件核查结果

### Transit 现成组件

已核实 [Transit v1.4.5](https://github.com/yyy622hhh/komari-theme-transit/releases/tag/v1.4.5)，准确提交 `ee9f31c5ff104e033ded858171ce0b63c672e878`。Release 存在：

- `transit-route-probe-plugin.zip`：Komari 服务端伴生插件。
- `transit-route-probe-helper.sh`：节点助手。
- `transit-collect-return-route.sh`：节点本地采集脚本。

路径是节点主动向国内三网目标运行 traceroute，再将逐跳信息回传插件，主题据 ASN 序列显示线路。不是普通 Ping 的另一个图表，也不能只在 CA 测一次来代表其他十台服务器的回程。助手只主动出站，无需开启通用远程 Shell；现有 Agent 的远控禁用状态应保留。

上游内置北京、上海、广州目标。我们的常驻昆明、南昌目标并非直接现成支持，不能假定把六条 Ping 目标填入就能完成路线采集，后续须核查适合的固定目标及两端白名单。

### 本 Fork 已继承的功能

v1.2.1 源码已经有 `companion/enhanced-route-probe/` 与 `companion/helper/`，组件版本 0.3.0；主题含线路展示和管理入口。现有 [THIRD_PARTY.md](../THIRD_PARTY.md) 已记录 Transit 来源，并随代码保留 MIT 文本。

- 插件清单适配目标为 Komari 1.6.0，默认关闭，仅声明 Node 兼容及 HTTP routes。
- Helper 需要 Linux、Python >=3.10 和 traceroute，支持受限 IPv4 UDP/TCP 采集；不是 Komari Agent 替代品。
- 未明确启用 ASN 补全时，真实路径可能只有 IP 而没有 ASN，此时应显示未知，不能仅用 IP 前缀伪造确认结论。
- 上游没有完成可据以宣称生产可用的实时采集闭环；不能直接把其试验组件当作当前系统上已经可用的功能。CN2 GIA/GT 等商业类别也不能仅凭 ASN 完全认证。

建议先沿用已继承的 Enhanced 协议与 UI，补齐兼容、目标和采集验证；只有明确存在缺口时才移植 Transit 的具体模块，避免整套混装两套不兼容插件或存储格式。

### 本轮验证限制

- 本轮新增的汇率解析诊断使用六项独立合成场景验证：相关资产干扰、错配币种、缺少时间、重复歧义、无效报价和脚本内伪报价。它们不访问网络，不使用真实行情，不代表长期抓取稳定性。
- Windows：Node 24.22.1、Python 3.14.7。Python helper 测试因 Linux 专用 `fcntl` 无法启动。
- 现有 Node 协议测试 16 项中 15 项通过；私有存储一项因 Windows 的 `0666` 与要求的 POSIX `0600` 权限不符而失败。首次运行还缺少忽略的 `test-results` 父目录，建立后确认了权限限制。没有删断言或把失败改成跳过。
- 本机没有可用的 WSL Linux。Linux 权限、完整 Helper 测试、实际 Komari 插件兼容、真实 traceroute/ASN 和节点资源消耗都仍须后续验证；这些结果不能替代生产验收。
- 本轮没有在任意 VPS 安装、启用或执行回程探测，没有修改 Agent、Cloudflare、Nginx、Komari 设置或防火墙。

## 多来源集成与许可

GitHub 当前 Fork 的直接父仓库仍为 casiuna/Glassmorphism-Enhanced；一个项目可以包含多个许可明确的来源，不需要“同时 Fork 两个父项目”。Fork 关系不能代替许可义务。

实际复制或改编代码时，记录项目、准确提交、采用文件及修改范围，保留相关源文件的版权说明、完整许可，并更新 README/THIRD_PARTY 及安装 ZIP 内的许可文件。单独写一句“参考某项目”不一定足够。

- Transit：已核实 [MIT](https://github.com/yyy622hhh/komari-theme-transit/blob/ee9f31c5ff104e033ded858171ce0b63c672e878/LICENSE)，复用时保留其版权和许可文本。
- Transit 分类逻辑声明参考的 [oneclickvirt/backtrace](https://github.com/oneclickvirt/backtrace) 当前为 Apache-2.0，并非所有相关代码都是 MIT。若引入其受该许可约束的代码，应遵守 [Apache 2.0 第 4 节](https://www.apache.org/licenses/LICENSE-2.0)，保留所需声明和许可、标明修改；源包若包含 NOTICE，按其要求保留。此次只读源码树中未发现单独 NOTICE，实际采用时仍按固定提交复核。
- 公开 ASN 名称和自行实现的协议不能与复制别人代码混为一谈；仅根据实际采用的代码建立授权清单，不替上游未核实的授权链作保证。

本轮没有导入新的 Transit/backtrace 代码，也没有新增第二个 Fork 或更改项目许可证。未来的集成 PR 应同时交付相应来源及许可变更。
