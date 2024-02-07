$(document).ready(function (e) {
	$("#send_cust_btn").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/send",
            data: {'customer_send_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
	$("#send_cust_due_btn").on("click", function () {
		$.ajax({
            url: "/my/customer_statements/send",
            data: {'customer_send_overdue_statement':true},
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);
                if (datas.msg){
                	alert(datas.msg);
                }
            },
        });
	});
});