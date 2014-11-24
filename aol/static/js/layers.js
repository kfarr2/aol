var layers = (function(){
    // at the end of this closure we return an object containing all the layers

    // base layer for the map
    var natural_layer = new OpenLayers.Layer.XYZ("Naturalistic", "http://gis.rc.pdx.edu/arcgis/rest/services/aol/nlcd/MapServer/tile/${z}/${y}/${x}", {
        sphericalMercator: false,
        transitionEffect: 'resize',
        tileOrigin: new OpenLayers.LonLat(-300000, 2763954),
        format: "jpg",
        isBaseLayer: true,
        // this layer requires a custom function to retrieve the correct tile
        // from the tile server
        getURL: function(bounds){
            // constructs the proper URL for the tile img
            var res = this.map.getResolution();
            var x = Math.round((bounds.left - this.tileOrigin.lon) / (res * this.tileSize.w));
            var y = Math.round((this.tileOrigin.lat - bounds.top) / (res * this.tileSize.h));
            var z = this.map.getZoom();

            if ( ( x < 0 ) || ( y < 0 ) || ( z < 0 ) ) {
                return null;
            }

            var url = this.url;
            var s = '' + x + y + z;
            if ( url instanceof Array ) {
                url = this.selectUrl(s, url);
            }

            var path = OpenLayers.String.format(url, {'x': x, 'y': y, 'z': z});

            return path;
        }
    });

    var ownership_layer = new OpenLayers.Layer.XYZ("Ownership", "http://gis.rc.pdx.edu/arcgis/rest/services/aol/ownership/MapServer/tile/${z}/${y}/${x}", {
        sphericalMercator: false,
        transitionEffect: 'resize',
        tileOrigin: new OpenLayers.LonLat(-300000, 2763954),
        format: "jpg",
        isBaseLayer: true,
        // this layer requires a custom function to retrieve the correct tile
        // from the tile server
        getURL: function(bounds){
            // constructs the proper URL for the tile img
            var res = this.map.getResolution();
            var x = Math.round((bounds.left - this.tileOrigin.lon) / (res * this.tileSize.w));
            var y = Math.round((this.tileOrigin.lat - bounds.top) / (res * this.tileSize.h));
            var z = this.map.getZoom();

            if ( ( x < 0 ) || ( y < 0 ) || ( z < 0 ) ) {
                return null;
            }

            var url = this.url;
            var s = '' + x + y + z;
            if ( url instanceof Array ) {
                url = this.selectUrl(s, url);
            }

            var path = OpenLayers.String.format(url, {'x': x, 'y': y, 'z': z});

            return path;
        }
    });

    // layer for drawing the lake outlines
    var lakes_kml_layer = new OpenLayers.Layer.Vector("KML", {
        projection: new OpenLayers.Projection("EPSG:4326"),
        strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1})],
        protocol: new OpenLayers.Protocol.HTTP({
            url: '/map/lakes.kml',
            params: {},
            format: new OpenLayers.Format.KML({
                extractStyles: true,
                extractAttributes: true,
                maxDepth: 16
            })
        }),
        styleMap: new OpenLayers.StyleMap({
            default: new OpenLayers.Style(),
            select: new OpenLayers.Style(),
        }),
        minScale: 432002,
        maxScale: 1
    });

    // don't have a clue why this is needed. Pulled out and simplified from the old AOL code
    lakes_kml_layer.initResolutions = function(){
        this.maxResolution = OpenLayers.Util.getResolutionFromScale(this.options.minScale, this.map.units);
        this.minResolution = OpenLayers.Util.getResolutionFromScale(this.options.maxScale, this.map.units);
        this.maxScale = OpenLayers.Util.getScaleFromResolution(this.minResolution, this.units);
        this.minScale = OpenLayers.Util.getScaleFromResolution(this.maxResolution, this.units);
    };


    // layer for drawing the lake outlines
    var facilities_kml_layer = new OpenLayers.Layer.Vector("KML", {
        projection: new OpenLayers.Projection("EPSG:4326"),
        strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1})],
        protocol: new OpenLayers.Protocol.HTTP({
            url: '/map/facilities.kml',
            params: {},
            format: new OpenLayers.Format.KML({
                extractStyles: true,
                extractAttributes: true,
                maxDepth: 16
            })
        }),
        styleMap: new OpenLayers.StyleMap({
            default: new OpenLayers.Style(),
            select: new OpenLayers.Style(),
        }),
        minScale: 54001,
        maxScale: 1
    });

    // don't have a clue why this is needed. Pulled out and simplified from the old AOL code
    facilities_kml_layer.initResolutions = lakes_kml_layer.initResolutions

    // return all the layers with friendly names
    return {natural_layer: natural_layer, ownership_layer: ownership_layer, lakes_kml: lakes_kml_layer, facilities_kml: facilities_kml_layer}
})()
