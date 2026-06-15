<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor
    xmlns="http://www.opengis.net/sld"
    xmlns:sld="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"
    version="1.0.0">

  <sld:NamedLayer>
    <sld:Name>gis_osm_buildings_a_free_1</sld:Name>
    <sld:UserStyle>
      <sld:Title>Buildings (Area) - OSM Carto z17</sld:Title>
      <sld:Abstract>OSM Carto z17 style for Geofabrik gis_osm_buildings_a_free_1</sld:Abstract>
      <sld:IsDefault>1</sld:IsDefault>
      <sld:FeatureTypeStyle>
        <sld:Name>gis_osm_buildings_a_free_1_fts</sld:Name>
        <sld:Title>Buildings (Area) - OSM Carto z17</sld:Title>
        <sld:SemanticTypeIdentifier>generic:geometry</sld:SemanticTypeIdentifier>
        <sld:Rule>
          <sld:Name>building_fill</sld:Name>
          <sld:Title>building_fill</sld:Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>fclass</ogc:PropertyName>
              <ogc:Literal>buildings</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <sld:MinScaleDenominator>2500</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>5000</sld:MaxScaleDenominator>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#d9d0c9</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#b0a7a0</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.75</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer></sld:StyledLayerDescriptor>
