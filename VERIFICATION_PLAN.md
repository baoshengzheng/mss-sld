# SLD 验证方案

## 验证层级总览

```
Level 0: 静态检查（自动化，0 数据依赖）     ← verify_sld.py
Level 1: 可视化对比（需 Shapefile + QGIS）
Level 2: 服务端集成（需 GeoServer + WMS）
Level 3: 参考对比（需 OSM Carto 瓦片）
```

---

## Level 0 — 静态自动化检查

### 0.1 XML 合法性
```bash
python verify_sld.py
```
验证项：
- 20 个 .sld 文件均为合法 XML
- SLD 1.0 命名空间正确
- 每个文件包含 NamedLayer → UserStyle → FeatureTypeStyle → Rule 完整链
- 每个 Rule 含 ScaleDenominator 约束

### 0.2 fclass 覆盖率
- 从 `geofabrik_schema.yaml` 提取全部 322 个 fclass 值
- 与 SLD 中的 `<ogc:Literal>` 值做集合对比
- 当前结果：322/322 = 100%

### 0.3 样式值正确性
- 从 OSM Carto 源码（`.mss` 文件）提取 z17 预期值
- 与 SLD 中的 CssParameter 做精确对比
- 覆盖：13 种道路、14 种土地利用、建筑物、水域

### 0.4 SLD Schema 验证（可选）
```bash
# 下载 OGC SLD 1.0 XSD
wget http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd

# 用 xmllint 做 schema 验证
for f in sld/*.sld; do
    xmllint --noout --schema StyledLayerDescriptor.xsd "$f" && echo "OK: $f"
done
```

---

## Level 1 — QGIS 可视化验证

### 准备工作

1. 下载测试数据（选择一个城市级别的 shapefile，数据量适中）：
   ```
   https://download.geofabrik.de/europe/germany/berlin.html
   → 下载 berlin-latest-free.shp.zip
   ```

2. 解压得到全部 shapefile：
   ```
   gis_osm_roads_free_1.shp
   gis_osm_buildings_a_free_1.shp
   gis_osm_landuse_a_free_1.shp
   gis_osm_water_a_free_1.shp
   gis_osm_waterways_free_1.shp
   gis_osm_places_free_1.shp
   gis_osm_pois_free_1.shp
   ... 等
   ```

### 1.1 图层加载与样式绑定

在 QGIS 中逐个加载 shapefile 并绑定 SLD：

| Shapefile | SLD 文件 |
|-----------|---------|
| `gis_osm_roads_free_1.shp` | `gis_osm_roads_free_1.sld` |
| `gis_osm_buildings_a_free_1.shp` | `gis_osm_buildings_a_free_1.sld` |
| `gis_osm_landuse_a_free_1.shp` | `gis_osm_landuse_a_free_1.sld` |
| `gis_osm_water_a_free_1.shp` | `gis_osm_water_a_free_1.sld` |
| `gis_osm_waterways_free_1.shp` | `gis_osm_waterways_free_1.sld` |
| `gis_osm_places_free_1.shp` | `gis_osm_places_free_1.sld` |
| `gis_osm_pois_free_1.shp` | `gis_osm_pois_free_1.sld` |
| `gis_osm_railways_free_1.shp` | `gis_osm_railways_free_1.sld` |
| `gis_osm_traffic_free_1.shp` | `gis_osm_traffic_free_1.sld` |
| `gis_osm_transport_free_1.shp` | `gis_osm_transport_free_1.sld` |
| `gis_osm_pois_a_free_1.shp` | `gis_osm_pois_a_free_1.sld` |
| `gis_osm_traffic_a_free_1.shp` | `gis_osm_traffic_a_free_1.sld` |
| ... | ... |

**QGIS 操作步骤**：
1. `Layer → Add Layer → Add Vector Layer` → 选择 shapefile
2. 右键图层 → `Properties → Symbology`
3. 左下角 `Style → Load Style` → 选择对应的 `.sld` 文件
4. 缩放至 1:2000 级别（QGIS 状态栏的 Scale 框输入 `2000`）

### 1.2 逐图层检查清单

#### 道路图层 (roads)
- [ ] motorway: 粉红填充 `#e892a2`，外轮廓 `#dc2a67`，宽度 12/18px
- [ ] primary: 淡橙填充 `#fcd6a4`，外轮廓 `#a06b00`
- [ ] residential: 白色填充 `#ffffff`，外轮廓 `#bbbbbb`，宽度 7/12px
- [ ] footway: 鲑鱼色填充 `#fa8072`，虚线 `2,4`，宽度 0.9/1.3px
- [ ] cycleway: 蓝色填充 `#0000ff`，虚线 `4,4`，宽度 0.6/0.9px
- [ ] track: 棕色填充 `#996600`，宽度 1.2/1.5px
- [ ] 道路文字标注（如道路名）

#### 建筑物图层 (buildings)
- [ ] 米色填充 `#d9d0c9`，深色边框 `#b0a7a0`，线宽 0.75px
- [ ] 建筑物之间无边线重叠异常

#### 土地利用图层 (landuse)
- [ ] 森林 `#add19e`，公园 `#c8facc`，住宅 `#e0dfdf`
- [ ] 工业区 `#ebdbe8`，商业区 `#f2dad9`
- [ ] 颜色无越界/错配

#### 水域图层 (water + waterways)
- [ ] 水面 `#aad3df`
- [ ] 河流宽度 10px，运河 14px，溪流 3.5px
- [ ] 冰川 `#ddecec` + 蓝色虚线边框

#### 地名图层 (places)
- [ ] 城市名 15pt 黑色，halo 白底
- [ ] 村镇名 12pt
- [ ] 标注不重叠不拥挤

#### POI 图层 (pois)
- [ ] 餐饮橙色点 `#C77400`，住宿蓝色 `#0092da`
- [ ] 医疗红色 `#BF0000`，商业紫色 `#ac39ac`
- [ ] z17 尺度下有文字标注

#### 铁路图层 (railways)
- [ ] 干线深灰 `#666666`，宽 2.5px
- [ ] 地铁虚线 `8,6`，有轨电车 1.5px

#### 交通图层 (traffic)
- [ ] 交通信号灯、停车场、加油站标记
- [ ] 图标尺寸 6-8px

#### 行政边界 (adminareas)
- [ ] 国界紫色 `#8d618b`，宽 7px
- [ ] 下级边界逐级减细

### 1.3 截图对比

在 QGIS 中对同一区域（如柏林市中心）截图，与 OSM 官网 z17 截图对比：
- 打开 [openstreetmap.org](https://www.openstreetmap.org/#map=17/52.5163/13.3777) 对比
- 重点对比：道路颜色层级、建筑密度、水面渲染、字体大小

---

## Level 2 — GeoServer 服务端验证

### 2.1 环境准备

```bash
# Docker 方式启动 GeoServer（推荐）
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/sld:/opt/geoserver/data_dir/styles \
  -v $(pwd)/berlin_data:/opt/geoserver/data_dir/data/berlin \
  -e GEOSERVER_ADMIN_USER=admin \
  -e GEOSERVER_ADMIN_PASSWORD=geoserver \
  docker.osgeo.org/geoserver:2.25.x
```

### 2.2 发布图层并绑定 SLD

1. 登录 `http://localhost:8080/geoserver`
2. 创建 Workspace（如 `osm`）
3. 创建 Store → Shapefile → 上传 shapefile
4. 发布图层 → Publishing tab
   - Default Style: 选择对应的 SLD 样式
   - 确认 Declared SRS: `EPSG:4326`
5. 重复上述步骤发布所有图层

### 2.3 图层组验证

创建 Layer Group 按 OSM Carto 顺序排列图层：

```
1. landuse_a         (面 - 底层)
2. water_a           (面)
3. waterways         (线)
4. buildings_a       (面)
5. roads             (线)  ← casing 先渲染
6. railways          (线)
7. adminareas_a      (面)
8. places            (点)
9. pois              (点)
10. traffic           (点)
11. transport         (点)
```

### 2.4 WMS GetMap 验证

```bash
# 发送 WMS GetMap 请求验证 z17 级别
curl "http://localhost:8080/geoserver/osm/wms?\
SERVICE=WMS&\
VERSION=1.3.0&\
REQUEST=GetMap&\
LAYERS=osm:roads,osm:buildings_a,osm:landuse_a,osm:water_a&\
BBOX=13.37,52.51,13.38,52.52&\
CRS=EPSG:4326&\
WIDTH=800&\
HEIGHT=600&\
FORMAT=image/png&\
STYLES=" > test_z17.png
```

### 2.5 性能检查

- WMS GetMap 响应时间 < 500ms（单层）
- 图层组完整渲染时间 < 2s
- 无渲染异常（白屏、空图、样式丢失）

---

## Level 3 — 与 OSM Carto 官网对比

### 3.1 对比方法

1. 在 GeoServer 中导出 z17 WMS 图片
2. 从 openstreetmap.org 截取同区域同级别的 PNG 瓦片
3. 使用图像对比工具逐像素比较

### 3.2 对比维度

| 维度 | 检查内容 |
|------|---------|
| 道路颜色 | motorway/trunk/primary/residential/footway 色调 |
| 道路宽度 | 各级道路在 z17 的相对宽度比例 |
| 建筑颜色 | `#d9d0c9` vs OSM Carto 建筑颜色 |
| 水面颜色 | `#aad3df` vs OSM Carto 水面 |
| 绿地颜色 | forest/park/grass 差异 |
| 文字大小 | 地名标注在相同 DPI 下的大小 |
| Halo 效果 | 文字白边的透明度和宽度 |

### 3.3 已知差异（预期存在）

这些差异无法在 SLD 1.0 中消除：

- **SVG 图标**：OSM Carto 使用定制 SVG 图标，SLD 使用标准几何标记（circle/square/triangle）
- **道路连接处理**：Mapnik 的 `line-join: round` 效果与 GeoServer 实现可能有细微差异
- **文字避让**：OSM Carto 有复杂的 `text-padding`/`shield-placement` 逻辑，SLD 1.0 仅支持基础避让
- **隧道虚线**：虚线间距渲染可能因渲染引擎实现而异
- **Pattern 填充**：military 的斜线填充、wetland 图案在 SLD 中需 ExternalGraphic

---

## 快速参考：验证命令

```bash
# Level 0: 静态自动化检查（0 依赖，30 秒完成）
python verify_sld.py

# 重新生成全部 SLD（修改样式后）
python generate_sld.py

# 单独生成某图层
python generate_sld.py --layer roads

# XML Schema 验证（需 xmllint）
find sld -name "*.sld" -exec xmllint --noout {} \;
```
