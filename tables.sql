CREATE TABLE messages (
	sender varchar(255),
	recipient varchar(255),
	sender_name varchar(255),
	sender_email varchar(255),
	subject varchar(255),
	msg_date datetime,
	payload text,
	id int auto_increment,
	primary key(id));
	

CREATE TABLE phone_numbers (
	message_id int,
	phone_number varchar(16)
);
