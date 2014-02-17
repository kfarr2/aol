// These are the required projections for use on the map (http://www.spatialreference.org/ref/epsg/3644/proj4js/)
Proj4js.defs["EPSG:3644"] = "+proj=lcc +lat_1=43 +lat_2=45.5 +lat_0=41.75 +lon_0=-120.5 +x_0=399999.9999984 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +to_meter=0.3048 +no_defs";

var MAP;
$(document).ready(function(){
    // map config
    var scales = [1728004.3888287468, 864002.1944143734, 432001.0972071867, 216000.5486035933, 108000.2743017966, 54000.1371508983, 27000.0685754491, 13500.0342877245, 6750.0171438622];
    var map_options = {
        maxExtent: new OpenLayers.Bounds(-330000, -200000, 2630000, 1900000),
        projection: new OpenLayers.Projection("EPSG:3644"),
        displayProjection: new OpenLayers.Projection("EPSG:4326"),
        numZoomLevels: scales.length,
        restrictedExtent: new OpenLayers.Bounds(127741, 4648, 2363853, 1733815),
        scales: scales,
        units: "ft"
    }

    // create the map, add the layers, and zoom to the initial location
    var map = new OpenLayers.Map('map', map_options);
    MAP = map;
    map.addLayer(layers.base);
    map.addLayer(layers.lakes_kml);
    map.addLayer(layers.facilities_kml);
    // when the map is moved update the kml layers since it lazily fetches
    // the KML from the server
    map.events.register("moveend", map, function(event){
        layers.lakes_kml.protocol.params.scale = Math.round(this.getScale());
        layers.lakes_kml.protocol.params.bbox_limited = this.getExtent().toBBOX();
        layers.lakes_kml.redraw(true);

        layers.facilities_kml.protocol.params.scale = Math.round(this.getScale());
        layers.facilities_kml.protocol.params.bbox_limited = this.getExtent().toBBOX();
        layers.facilities_kml.redraw(true);
    })

    // make the KML layers clickable
    var control = new OpenLayers.Control.SelectFeature([layers.lakes_kml, layers.facilities_kml])
    // this allows the map to be dragged when the mouse is down on one of this
    // layer's items
    control.handlers.feature.stopDown = false;
    map.addControl(control)
    control.activate()

    // when the lake kml is clicked notify the map
    layers.lakes_kml.events.register("featureselected", layers.lakes_kml_layer, function(evt){
        var feature = this.selectedFeatures[0];
        $('#map').trigger('lake:selected', {feature: feature});
        // we have to unselect the feature to be able to click it again,
        // without clicking on the map. It's lame
        control.unselectAll();
    });


    // render a popup window when a facility is clicked
    var popup = null;
    layers.facilities_kml.events.register("featureselected", layers.facilities_kml, function(event){
        var feature = this.selectedFeatures[0];
        if(popup) map.removePopup(popup);
        map.addPopup(popup = new OpenLayers.Popup.FramedCloud(
            "foo",
            event.feature.geometry.getBounds().getCenterLonLat(),
            null,
            event.feature.attributes.description,
            null,
            true,
            function(){
                map.removePopup(popup);
                // we have to unselect the feature to be able to click it again,
                // without clicking on the map. It's lame
                control.unselectAll();
            }
        ));
    });

    // If we don't preload the facility HTML on the page, when the balloon
    // window pops up, the facility image throws off the openlayers balloon
    // height calculatation (because it is calculated *before* the image height
    // is known)...so a scrollbar appears in the balloon. We don't want that,
    // so we preload all the HTML
    layers.facilities_kml.events.register("loadend", layers.facilities_kml, function(event){
        // remove all the existing preloaded stuff, since it's no longer relevent
        $('.preloaded-facility').remove()
        // for each feature, create a hidden div on the page that renders the
        // HTML (thus loading the image)
        for(var i = 0; i < this.features.length; i++){
            var data = this.features[i].data;
            $('body').append($('<div class="preloaded-facility"></div>').append(data.description).hide())
        }
    });

    // zoom the map
    var url = $.url();
    if(url.param('minx') && url.param('miny') && url.param('maxx') && url.param('maxy')){
        console.log("zoom");
        map.zoomToExtent(new OpenLayers.Bounds(url.param('minx'), url.param('miny'), url.param('maxx'), url.param('maxy')), true);
    } else {
        map.zoomToMaxExtent();
        map.setCenter(new OpenLayers.LonLat(1294408, 865759), 0);
    }

    $(document).on("map:zoomto", function(e){
        map.zoomToExtent(new OpenLayers.Bounds(e.minx, e.miny, e.maxx, e.maxy), true);
    });
});

