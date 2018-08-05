
let hw_admin = ((hw)=>{
    if(!hw){
        console.error("hw.js has to be declared before hw_admin.js")
        return;  
    } 
    let obj = {};
    //-Changes the content if any
    //-Shows a toast if there's a message
    obj.processResponse = (data)=>{
        if(data.msg) 
            hw.toast(data.msg)
        
        if(data.content){
            $('#hw_container').hide(200, ()=>{
                $('#hw_container').html(data.content)
                obj.initListeners()
                $('#hw_container').show(200)
            })
        }
    }

    obj.initListeners = ()=>{
        $("#hw-user-send").on("click", ()=>{
            hw.ajax_req({
                'get_lists': true,
                'email': $("#id_email").val()
            }, obj.processResponse)
        })
        $("#hw-requests-list li").on("click", (ev)=>{
            hw.ajax_req({
                'select_request': true,
                'request_id': ev.currentTarget.dataset.requestId
            }, obj.processResponse)
        })
        $("#hw-lendings-list li").on("click", (ev)=>{
            hw.ajax_req({
                'return_item': true,
                'lending_id': ev.currentTarget.dataset.lendingId
            }, obj.processResponse)
        })
        $("#hw-available-items-list li").on("click", (ev)=>{
            hw.ajax_req({
                'make_lending': true,
                'item_id': ev.currentTarget.dataset.itemId,
                'request_id': ev.currentTarget.parentNode.dataset.requestId
            }, obj.processResponse)
        })
    }
   

    
    return obj
})(hw)


document.addEventListener("DOMContentLoaded", ()=>{
    hw_admin.initListeners()
})