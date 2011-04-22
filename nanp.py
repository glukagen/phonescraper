# thanks to this thread: http://stackoverflow.com/questions/123559/a-comprehensive-regex-for-phone-number-validation
import re
nanp_pattern = '(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'
number_re = re.compile(nanp_pattern)
email_msg = '''
Hey guys,

This is zakc. my digits are:

234 456.2428 x901 2.

Thanks! have a great one!
-Zachary
cell:+533456'''
x = number_re.findall(email_msg)
if x==[]:
	print 'no digits'
else:
	print x