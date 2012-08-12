(function($){

    window.Entry = Backbone.Model.extend({});

    window.Entries = Backbone.Collection.extend({
        model: Entry,
        url: '/entries/'
    });

    window.EntryView = Backbone.View.extend({
        template:'#entry-template-full',//detailed view
        className: 'entry',

        events: {
            'click .delete-entry': 'deleteEntry',
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.initializeTemplate();
        },
        initializeTemplate: function(){
            this.template = _.template($(this.template).html());
        },
        render: function(eventName){
            obj = this.model.toJSON();
            obj['pub_format'] = Helpers.formatDate(obj['pub_date']);
            $(this.el).html(this.template(obj));
            return this;
        },
        deleteEntry: function(){
            this.model.destroy({
                success: function() {
                    entry_id = window.location.hash.split('/')[1]
                    if(App.forid) delete App.forid;
                    App.navigate('', true);
                    Helpers.createAutoClosingAlert('Successfully deleted the blog post with id: '+entry_id);
                }
            });
            return false;
        },
        close: function(){
            $(this.el).unbind();
            $(this.el).empty();
        }
    });

    window.LibraryEntryView = EntryView.extend({
        template: '#entry-template-small',
        className: 'entry span4'
    });

    window.LibraryView = Backbone.View.extend({

        initialize: function() {
            _.bindAll(this, 'render');
            this.template = _.template($('#library-template').html());
            this.collection.bind('reset', this.render);
        },
        render: function() {
            var $entries,
                collection = this.collection;
            $(this.el).html(this.template());
            $entries = this.$('.entries');
            collection.each(function(entry){
                var view = new LibraryEntryView({
                    model: entry,
                    collection: collection
                });
                $entries.append(view.render().el);
            });
            return this;
        }
    });

    window.EditCreateView = Backbone.View.extend({
        template: '#new-entry-template',
        tagName: 'form',
        className: 'form-horizontal',

        events:{
            'click .cancel': 'cancelEntry',
            'click .save': 'saveEntry'
        },
        initialize: function(){
            this.initializeTemplate();
        },
        initializeTemplate: function(){
            this.template = _.template($(this.template).html());
        },
        render: function(data){
            $(this.el).html(this.template());
            return this;
        },
        cancelEntry: function(){
            App.navigate('', true);
            return false;
        },
        saveEntry: function(){
            var attrs = ({
                 'title': this.$('#input01').val(),
                 'body_markdown': epiceditor.exportFile()
             });
             console.log(attrs.body_markdown);
             if(this.model.isNew()){
                 var self = this;
                 App.library.create(attrs, {
                     success: function(data){
                         epiceditor.unload();
                         if(App.forid) delete App.forid;//always go to home
                         App.navigate('', true);
                         Helpers.createAutoClosingAlert('Successfully created new blog post');
                     }
                 })
             }
             else{
                 this.model.save(attrs, {
                     success: function(model, response){
                         epiceditor.unload();
                         App.navigate('', true);
                         Helpers.createAutoClosingAlert('Successfully edited' +
                         ' the blog post with id: '+response['id'])
                     }
                });
             }
             return false;
        }
    });
    
    window.NavbarView = Backbone.View.extend({
        tagName: 'ul',
        className: 'nav',
        events: {
            'click .new-entry': 'newEntry'
        },       
        initialize: function(){
            _.bindAll(this, 'render');
            this.template = _.template($('#header-template').html());
        },
        render: function(){
            $(this.el).html(this.template());
            return this;
        },
        newEntry: function(){
            App.navigate('entries/new', true);
            return false;
        }
    });

    window.BlogApp = Backbone.Router.extend({
        routes: {
            '':'home',
            'entries/new': 'create_new_blog_post',
            'entries/:id/edit': 'edit_blog_post',
            'entries/:id': 'show_blog_post'
        },
        initialize: function(){
            $('.nav').append(new NavbarView().render().el);
        },
        home: function(callback) {
            this.library = new Entries();
            this.LibraryView = new LibraryView({
                collection: this.library
            });
            var self = this;
            this.library.fetch({
                success: function(){
                   if(callback && typeof(callback) === 'function'){
                        callback.apply(self, [self.forid]);
                   } else {
                        $('.hero-unit').empty().append($('.initial-message').html());
                        var $container = $('.row');
                        $container.empty();
                        $container.append(self.LibraryView.render().el);
                   }
                }
            });
        },
        show_blog_post: function(id) {
            if(this.library){
                this.blog_post_view = new EntryView({model: this.library.get(id)})
                $('.row').empty();
                var $container = $('.hero-unit');
                $container.empty();
                $container.append(this.blog_post_view.render().el);
            } else {
                this.forid = id;
                this.home(App.show_blog_post);
            }
        },
        create_new_blog_post: function() {
            if(this.library){
                $('.hero-unit').empty().append('<h1>Create new blog post.</h1>'); 
                this.new_blog_post_view = new EditCreateView({model: new Entry()});
                $('.row').empty().append(this.new_blog_post_view.render().el);
                var script =  document.createElement('script');
                script.type = 'text/javascript';
                script.src = 'static/js/epiceditor.js';
                $('body').append(script);
            } else {
                this.home(App.create_new_blog_post);
            }
        },
        edit_blog_post: function(id) {
            if(this.library) {
                if(this.forid) delete this.forid;
                var model = this.library.get(id);
                var edit_view = new EditCreateView({model: model});
                $('.hero-unit').empty().append('<h1>Edit blog post.</h1>'); 
                $('.row').empty().append(edit_view.render().el);
                var script =  document.createElement('script');
                script.type = 'text/javascript';
                script.src = 'static/js/epiceditor.js';
                $('body').append(script);
                $('#input01').val(model.get('title'));
                epiceditor.importFile(null, model.get('body_markdown'));
            } else {
                this.forid = id;
                this.home(App.edit_blog_post);
            }
        }
    });

    $(document).ready(function(){
        window.App = new BlogApp();
        Backbone.history.start();
    });

    var Helpers = {
        createAutoClosingAlert: function(msg){
            $('.container:eq(1)').prepend('<div class="alert alert-error fade in">' + 
                                            '<button type="button" class="close" data-dismiss="alert">x</button>'+
                                            msg+'</div>'
                                            );
            var alert = $('.alert').alert();
            window.setTimeout(function(){alert.alert('close')}, 4000);
        },
        formatDate: function(d){
            a = d.split(' ');
            pub_str = 'Posted ' + a[0] + ' days ago on ' +
                        a[1] + ' ' + parseFloat(a[2]) + ', ' + a[3] + ' by ';
            return pub_str;
        }

    }
})(jQuery);
