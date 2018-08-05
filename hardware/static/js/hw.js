let hw = (()=>{
    let obj = {}
    //Sends an ajax request using POST
    //The response must be an html string
    obj.ajax_req = (data, cb)=>{
        data['csrfmiddlewaretoken'] = window.CSRF_TOKEN
        success: cb || function(){}
        $.ajax({
            method: 'POST',
            data: data,
            success: success
        })
    }

    obj.toast = (msg)=>{
        $.snackbar({
            content: msg,
            timeout: 3000
        })
    }


    return obj
})()
