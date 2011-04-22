<?php

ini_set('pcre.backtrack_limit', 1000000);

mysql_connect(':/tmp/mysql.sock','root','');
mysql_select_db('dijscrape');

function show_data() {
  $id = $_REQUEST['message_id'];
  $query = "SELECT * from messages where messages.id = $id;";
  $res = mysql_query($query);
  while($row = mysql_fetch_assoc($res)) {
    echo json_encode($row);
    return;
  }
}

echo mysql_error();
show_data();
