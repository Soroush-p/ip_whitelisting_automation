   
removeRow = function(el) {
    // remove the corresponding row of the table and
    // when the table is empty diables the submit button
    $(el).closest("tr").remove()
    var row = $("#tbl_schl > tbody > tr").length
    if (row == 1){
        $("#btn_sbmt").prop('disabled', true);
    }
}

function validateCIDR(cidr) {
    // Regular expression to validate IPv4 address format
    const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/;

    // Split the input into IP address and prefix length
    const parts = cidr.split('/');
    if (parts.length !== 2) {
        return false;
    }

    const ip = parts[0];
    const prefixLength = parts[1];

    // Validate the IP address using the regex
    if (!ipv4Regex.test(ip)) {
        return false;
    }

    // Validate the prefix length
    const prefix = parseInt(prefixLength, 10);
    if (isNaN(prefix) || prefix < 0 || prefix > 32) {
        return false;
    }

    return true;
}

$(document).ready(function()
    {
	$("#url_drpbx").change(function()
        {
	        // send selected value of drop box, in return populates other textboxes
	    var urlValue = $(this).serialize();
            //console.log(urlValue);
            $.ajax({url: "/api/view", data: urlValue ,type: "POST", dataType: "json", success: function (data)
               {
                //console.log(data);
		//console.log(Object.values(data)[1]);
                document.getElementById("firewall_txt").value = Object.values(data)[1];
                document.getElementById("mgmtIP_txt").value = Object.values(data)[3];
                document.getElementById("contextName_txt").value = Object.values(data)[2];
                document.getElementById("intin_txt").value = Object.values(data)[4];
                document.getElementById("intout_txt").value = Object.values(data)[5];
                document.getElementById("destination_txt").value = Object.values(data)[6];
                document.getElementById("port_txt").value = Object.values(data)[7];
                document.getElementById("nat_txt").value = Object.values(data)[8];
                //$("#firewall_txt").value = Object.values(data)[1];
                    }})
		});


		$("#add_btn").on('click', function(event){
        /*
            Adds a new row to the scheduling table of HTML DOM if
            there is no conflict with other rows in the table
        */
            event.preventDefault();
            var ipCidr = $("#IP_txt").val();
            var ipExists = false;

            if (!ipCidr){
                alert('Please enter the IP Address ');
                return;
            }

            // Check if the IP CIDR already exists in the table
            $("#iplist_tbl tr").each(function() {
                var rowIpCidr = $(this).find('td:first').text();
                if (rowIpCidr === ipCidr) {
                    ipExists = true;
                    return false; // Break the loop
                }
            });

            if (ipExists ){
                alert('IP CIDR already exists in the IP Address List table');
            } else if ( validateCIDR(ipCidr)) {
                $("#iplist_tbl").append("<tr class='tbl_row'><td>" + ipCidr + "</td><td><button onclick='removeRow(this)'>X</button></td></tr>");
                $("#IP_txt").val('');
            } else {
                alert('IP CIDR is not valid');
                //console.log(document.getElementById("iplist_tbl").value);
            }
        });
    

                
/*		    event.preventDefault();
			if (( $("#IP_txt").val() != null ) && validateCIDR($("#IP_txt").val())) {
                    
                    $("#iplist_tbl").append("<tr class=tbl_row><td style=width: 120px>" + $('#IP_txt').val() + "</td><td>" + '<button onclick="removeRow(this)">X</button></td></tr>');
                    //console.log(document.getElementById("iplist_tbl").value);
                    //document.getElementById("iplist_tbl").append("<tr class='tbl_row'><td style='width: 120px'></td><td><button onclick='removeRow(this)'>X</button></td></tr>");
      
                       }
                       else
                       {
                        alert('IP CIDR is not valid');
                        console.log(document.getElementById("iplist_tbl").value);
                       }
              })

*/


    	$("#codeGenerate-btn").on('click', function (event) {
            event.preventDefault();
            //$("#result").text("");
            //$("#result1").text("");
            var arrData = [];
            var arrformdata = [];
            //loop over each table row (tr)
            $("#iplist_tbl tr").each(function () {
                var currentRow=$(this);
                var ip_addr = currentRow.find("td:eq(0)").text();
                //console.log(ip_addr);
                // creates a object of table rows
                var obj={};
                obj.ip_addr=ip_addr;
                arrData.push(obj);
            });
            //console.log()           
            var context = document.getElementById("contextName_txt").value;
            var mgmtIP = document.getElementById("mgmtIP_txt").value;
            var intin = document.getElementById("intin_txt").value;
            var intout = document.getElementById("intout_txt").value;
            var firewall = document.getElementById("firewall_txt").value;
            var port = document.getElementById("port_txt").value;
            var dstip = document.getElementById("destination_txt").value;
            var customername = document.getElementById("customername_txt").value;
            var nat = document.getElementById("nat_txt").value;
            var mydata = {'table': arrData, 'context': context, 'mgmtIP': mgmtIP, 'intin': intin, 'intout': intout, 'firewall': firewall, 'dstip': dstip, 'port':port, 'nat':nat, 'customername': customername};
            $.post('/form', mydata ,function (data) {
              document.forms['whitelistform']['txtar_code'].value = data ;
              $("#push-btn").prop('disabled', false);
              //let x = document.getElementById("code_txtar"); 
              //x.value = data
              //$("#code_txtar").val('');
              //console.log(data)
              //alert('Scheduling was succesfully written in the file');      
                
            });
        });
       
        $("#push-btn").on('click', function (event) {
           event.preventDefault();
           var username = document.getElementById("username_txt").value;
           var password = document.getElementById("password_txt").value;
           var firewall = document.getElementById("firewall_txt").value;
           var code = document.getElementById("code_txtar").value;
           var mgmtIP = document.getElementById("mgmtIP_txt").value;
           var context = document.getElementById("contextName_txt").value;
           var data = {'code': code , 'username': username, 'password': password, 'firewall': firewall, 'mgmtIP': mgmtIP, 'context': context};
           
           //console.log(code);
           $.ajax({
                url: "/api/push", 
                data: data ,
                type: "POST", 
                dataType: "json", 
                success: function (response){
                    console.log(response);
                    //$("#code_txtar").value = Object.values(data)[1];
                    document.getElementById("code_txtar").value = Object.values(response);
                    $("#push-btn").prop('disabled', true);
                }
            })
        });
})

