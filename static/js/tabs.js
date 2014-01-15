(function($){
    $.fn.arcTabs = function(){
        var that = this;

        // helper that finds all the tabs and hides them
        var hideAllTabs = function(){
            that.find('.tab').each(function(){
                $(this).removeClass('active');
                var id = $(this).attr('href');
                var tab = $(id);
                tab.hide();
            })
        }

        var onClick = function(e){
            e.preventDefault(); 
            hideAllTabs();
            $(this).addClass('active');
            var id = $(this).attr('href');
            var tab = $(id);
            tab.show();
        }

        this.find('.tab').click(onClick);
        hideAllTabs();
        this.find('.tab:first').click()
    }
}(jQuery))
