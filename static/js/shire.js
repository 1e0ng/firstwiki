var shire = {};

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

shire.ajax = function(url, type, args, callback){
    return $.ajax({
        'type': type,
        'timeout': 60000,
        'url': url,
        'data': args,
        'dataType': 'json'
    }).done(function(data){
        if ('error_msg' in data) {
            alert('Sorry, but ' + data['error_msg']);
        }
        else if(callback){
            callback.call(this, data);
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        alert('Oops. I encountered something unexpected. \r\nDetail: ' + textStatus + " " + errorThrown);
    });
};

shire.post = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    return shire.ajax(url, 'post', args, callback);
};

shire.get = function(url, args, callback) {
    return shire.ajax(url, 'get', args, callback);
};

shire.gui_ajax = function(url, type, args, callback, ctrls){
    var old_status = [];
    for(var i = 0; i < ctrls.length; ++i){
        var ctrl = ctrls[i];
        old_status.push($(ctrl).prop('disabled'));
        old_status.push($(ctrl).text());
        $(ctrl).prop('disabled', true);
        $(ctrl).text('Processing...');
    }
    return shire.ajax(url, type, args, callback).always(function(){
        for(var i = 0; i < ctrls.length; ++i){
            var ctrl = ctrls[i];
            $(ctrl).prop('disabled', old_status[i*2]);
            $(ctrl).text(old_status[i*2+1]);
        }
    });
};

shire.gui_get = function(url, args, callback, ctrls){
    return shire.gui_ajax(url, 'get', args, callback, ctrls);
};

shire.gui_post = function(url, args, callback, ctrls){
    args._xsrf = getCookie("_xsrf");
    return shire.gui_ajax(url, 'post', args, callback, ctrls);
};

shire.clone = function(obj){
    return $.extend(true, {}, obj);
};

shire.escape_html = (function(){
    var entityMap = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#39;',
        "/": '&#x2F;'
    };

    return function (string) {
        return String(string).replace(/[&<>"'\/]/g, function (s) {
          return entityMap[s];
        });
    };
})();

shire.unescape_html = (function(){
    var entityMap = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        '&quot;': '"',
        '&#39;': "'",
        '&#x2F;': "/"
    };

    return function (string) {
        return String(string).replace(/(&amp;|&lt;|&gt;|&quot;|&#39;|&#x2F)/g, function (s) {
          return entityMap[s];
        });
    };
})();
