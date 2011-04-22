<?php

ini_set('pcre.backtrack_limit', 1000000);

//$q = $_REQUEST['q'];
$q='';

mysql_connect(':/tmp/mysql.sock','root','');
mysql_select_db('dijscrape');
echo mysql_error();

function show_data() {
//$query = "SELECT phone_number,sender,recipient from phone_numbers,messages where phone_numbers.message_id=messages.id and phone_number not like '800%' group by phone_number";
//$query = "SELECT phone_number,sender,recipient,message_id from phone_numbers,messages where phone_numbers.message_id=messages.id and phone_number not like '800%' group by phone_number";
  $query = "SELECT * from phone_numbers,messages where (phone_numbers.message_id=messages.id and phone_number not like '800%' and (sender_name LIKE '$q%' OR sender_email LIKE '$q%' or phone_number LIKE '$q%')) group by phone_number";
  $res = mysql_query($query);
  $arr = array();
  while($row = mysql_fetch_assoc($res)) {
    $table_info = array("sender_name" => $row['sender_name'], "sender_email" => $row['sender_email'], "phone_number" => $row['phone_number'], "message_id" => $row['message_id']);
    array_push($arr, $table_info);
  }
  echo json_encode($arr);
  echo mysql_error();
}

/*


(email, phone_number) => message_id
message_id => sender, recipient, subject, payload

*/
?>

<html>
<head>
<script type="text/javascript" src="jquery.js"></script>
<script type="text/javascript">
$(document).ready(function() {
  populate_rows();
	shade_rows();
	
	$("input").click(function() {
		if($(this).val() == 'search string here....') {
			$(this).val('');
		}		
	});
	$("input").keyup(function() {
		search_string = $(this).val().trim();
		$("tbody tr").each(function() {
			show_row = false;
			$(this).children().each(function() {
				cell_text = $(this).html();
				if(cell_text.indexOf(search_string)!=-1) {
					show_row = true;					
				}
			});
			if(!show_row) {
				$(this).hide();
			}
			else {
				$(this).show();
			}
		});
		shade_rows();		

    $('#sender').text('');
    $('#recipient').text('');
    $('#subject').text('');
    $('#payload').html('');

    var data = $('.data_row:visible');
    if (data.length > 0 && search_string.length > 0) {
      var datum = data.data('info');
      $.get('/phonebook.php', {'message_id': datum['message_id']}, function (datum) {
        var datum = JSON.parse(datum);
        $('#sender').text(datum['sender']);
        $('#recipient').text(datum['recipient']);
        $('#subject').text(datum['subject']);
        $('#payload').html(datum['payload']);
      });
    }

	});
	
		
});

function shade_rows() {
	$("tbody tr").filter(":visible").each(function(index,element) {
		if(index%2) {
			$(this).css('background','lightgrey');
		}
		else {
			$(this).css('background','white');
		}
	});
}

function populate_rows() {
  var data = <?php show_data(); ?>;
  $('#data_table').empty();
	var thead = $('<thead style="background:grey;font-weight:bold"><td>Name</td><td>Email</td><td>Number</td></thead>');
  $('#data_table').append(thead);
  for (var i=0; i<data.length; i++) {
    var datum = data[i];
    var pn = datum['phone_number'];
    pn = pn.slice(0,3)+'-'+pn.slice(3,6)+'-'+pn.slice(6)
    var node = $('<tr class="data_row" id="row'+i+'"><td>'+ (datum['sender_name'] || '') +'</td><td>'+datum['sender_email']+'</td><td>'+pn+'</td></tr>');
    node.data('info', datum);
    $('#data_table').append(node);
  }
}
</script>
</head>
<body>
<div id="search_area" style="float:left">
	
filter text: <input type="text" size=50 value="search string here...."><br /><br />

(you can filter by name, email, digits in number...)<br /><br />

<table id='data_table'>
</table>
</div>
<div id="prevpane" style="float:right;width:50%;background:blue;padding-right:10%">
FROM: <span id="sender"></span><br /> 
TO: <span id="recipient"></span><br />
SUBJECT: <span id="subject"></span><br /><br />
<span id="payload"></span>
	
</div>


</body>
</html>
