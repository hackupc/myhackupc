let hw_list = ((hw)=>{
    if(!hw){
        console.error("hw.js has to be declared before hw_list.js")
        return;  
    } 
    let obj = {}
    obj.initListeners = ()=>{
        $(".hw-req-btn").on("click", (ev)=>{
            hw.ajax_req({
                'req_item':true, 
                'item_id': ev.target.dataset.itemId,
            }, (data)=>{
                if(data.msg) hw.toast(data.msg)
            })
        })
    }
    return obj
})(hw)

document.addEventListener("DOMContentLoaded", ()=>{
    hw_list.initListeners()
})