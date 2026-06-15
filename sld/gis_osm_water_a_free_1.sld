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
    <sld:Name>gis_osm_water_a_free_1</sld:Name>
    <sld:UserStyle>
      <sld:Name>gis_osm_water_a_free_1_style</sld:Name>
      <sld:Title>Water Bodies (Area) - OSM Carto z17</sld:Title>
      <sld:Abstract>OSM Carto z17 style for Geofabrik gis_osm_water_a_free_1</sld:Abstract>
      <sld:IsDefault>1</sld:IsDefault>
      <sld:FeatureTypeStyle>
        <sld:Name>gis_osm_water_a_free_1_fts</sld:Name>
        <sld:Title>Water Bodies (Area) - OSM Carto z17</sld:Title>
        <sld:SemanticTypeIdentifier>generic:geometry</sld:SemanticTypeIdentifier>
        <sld:Rule>
          <sld:Name>water_body</sld:Name>
          <sld:Title>water_body</sld:Title>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>water</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>reservoir</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>river</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>dock</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <sld:MinScaleDenominator>2500</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>5000</sld:MaxScaleDenominator>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#aad3df</sld:CssParameter>
            </sld:Fill>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>water_glacier</sld:Name>
          <sld:Title>water_glacier</sld:Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>fclass</ogc:PropertyName>
              <ogc:Literal>glacier</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <sld:MinScaleDenominator>2500</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>5000</sld:MaxScaleDenominator>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#ddecec</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#9cf</sld:CssParameter>
              <sld:CssParameter name="stroke-width">1.5</sld:CssParameter>
              <sld:CssParameter name="stroke-dasharray">4 2</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>water_wetland</sld:Name>
          <sld:Title>water_wetland</sld:Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>fclass</ogc:PropertyName>
              <ogc:Literal>wetland</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <sld:MinScaleDenominator>2500</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>5000</sld:MaxScaleDenominator>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#b5d0d0</sld:CssParameter>
              <sld:CssParameter name="fill-opacity">0.5</sld:CssParameter>
            </sld:Fill>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>water_label</sld:Name>
          <sld:Title>water_label</sld:Title>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>water</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>reservoir</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>fclass</ogc:PropertyName>
                <ogc:Literal>river</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <sld:MinScaleDenominator>2500</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>5000</sld:MaxScaleDenominator>
          <sld:TextSymbolizer>
            <sld:Label>
              <ogc:PropertyName>name</ogc:PropertyName>
            </sld:Label>
            <sld:Font>
              <sld:CssParameter name="font-family">Noto Sans Italic, Arial Italic, sans-serif</sld:CssParameter>
              <sld:CssParameter name="font-size">10</sld:CssParameter>
              <sld:CssParameter name="font-style">normal</sld:CssParameter>
              <sld:CssParameter name="font-weight">normal</sld:CssParameter>
            </sld:Font>
            <sld:LabelPlacement>
              <sld:PointPlacement>
                <sld:AnchorPoint>
                  <sld:AnchorX>0.5</sld:AnchorX>
                  <sld:AnchorY>0.5</sld:AnchorY>
                </sld:AnchorPoint>
                <sld:Displacement>
                  <sld:DisplacementX>0</sld:DisplacementX>
                  <sld:DisplacementY>-10</sld:DisplacementY>
                </sld:Displacement>
              </sld:PointPlacement>
            </sld:LabelPlacement>
            <sld:Fill>
              <sld:CssParameter name="fill">#4d80b3</sld:CssParameter>
            </sld:Fill>
            <sld:Halo>
              <sld:Radius>1</sld:Radius>
              <sld:Fill>
                <sld:CssParameter name="fill">rgba(255,255,255,0.6)</sld:CssParameter>
              </sld:Fill>
            </sld:Halo>
          </sld:TextSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer></sld:StyledLayerDescriptor>
