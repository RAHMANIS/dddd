# -*- coding: utf-8 -*-
import scrapy
import csv
import re
import sys
import json
import os
import os.path
import requests

from DELHI_SLDC import settings
from scrapy import signals
from pydispatch import dispatcher
from scrapy.utils.response import open_in_browser
import datetime
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from apscheduler.schedulers.twisted import TwistedScheduler


class DelhiSpider(scrapy.Spider):
	name = 'delhi'
	start_urls = ['https://www.delhisldc.org/dswebpage.aspx']
	
	# download_delay = 2.0
	


	def parse(self, response):
		month = response.xpath('//*[@id="ContentPlaceHolder2_ddmonth"]/option[@selected]/@value').extract_first()
		date = response.xpath('//*[@id="ContentPlaceHolder2_ddday"]/option[@selected]/@value').extract_first()
		year = response.xpath('//*[@id="ContentPlaceHolder2_txtyear"]/@value').extract_first()
		revision_num = response.xpath('//*[@id="ContentPlaceHolder2_ddrevnon"]/option[@selected]/@value').extract_first()
		timestamp = response.xpath('//span[contains(.,"Issued on")]/following::td[1]/span/text()').extract_first()
		print ('Revision Number =>', revision_num)
		print ('Timestamp Value =>', timestamp)
		
		
		csv_file = open("Results.csv", "r+", newline='', encoding='utf-8')
		file_size = os.path.getsize("Results.csv")
					
		Reader = csv.reader(csv_file)
		Datas = list(Reader)
		# csvfile = open("Results.csv", "w", newline='', encoding='utf-8')
		csv_wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
		for Constituent in response.xpath('//*[@id="ContentPlaceHolder2_cmbdiscom"]/option/@value').extract():
			print ('Constituent Name =>', Constituent)
			
			if file_size != 0:
				last_rev_num = Datas[-1][2]
				last_issue_date = Datas[-1][1]
				last_date = "".join(re.findall('^(\d+)',last_issue_date)).strip()
				last_month = "".join(re.findall('^\d+\D(\d+)\D\d+ ',last_issue_date)).strip()
			
			if file_size == 0:
				print ('\n\nStarting a New File\n\n')
				if 'BRPL' in Constituent:
					rq = scrapy.Request(response.url, callback=self.parse_results)
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['csv_wr'] = csv_wr
					rq.meta['Constituent'] = Constituent
					yield rq
				else:
					rq = scrapy.FormRequest(
						response.url,
							headers={
								'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
								'accept-language': 'en-US,en;q=0.9',
								'cache-control': 'max-age=0',
								'content-type': 'application/x-www-form-urlencoded',
								'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
								'referrerPolicy': 'strict-origin-when-cross-origin',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
								},

							formdata={
								'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
								'__EVENTARGUMENT':'',
								'__LASTFOCUS':'',
								'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
								'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
								'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
								'ctl00$ContentPlaceHolder2$ddmonth':month,
								'ctl00$ContentPlaceHolder2$ddday':date,
								'ctl00$ContentPlaceHolder2$txtyear':year,
								'ctl00$ContentPlaceHolder2$ddrevnon':revision_num,
							}, meta=response.meta, callback=self.parse_results)
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['csv_wr'] = csv_wr
					rq.meta['Constituent'] = Constituent
					yield rq
					
			else:
				rq = scrapy.FormRequest(
					response.url,
						headers={
							'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
							'accept-language': 'en-US,en;q=0.9',
							'cache-control': 'max-age=0',
							'content-type': 'application/x-www-form-urlencoded',
							'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
							'referrerPolicy': 'strict-origin-when-cross-origin',
							'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
							},

						formdata={
							'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
							'__EVENTARGUMENT':'',
							'__LASTFOCUS':'',
							'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
							'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
							'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
							'ctl00$ContentPlaceHolder2$ddmonth':month,
							'ctl00$ContentPlaceHolder2$ddday':date,
							'ctl00$ContentPlaceHolder2$txtyear':year,
							'ctl00$ContentPlaceHolder2$ddrevnon':revision_num,
						}, meta=response.meta, callback=self.parse_datewise)
				rq.meta['Reader'] = Reader
				rq.meta['Datas'] = Datas
				rq.meta['last_month'] = last_month
				rq.meta['last_date'] = last_date
				rq.meta['csv_wr'] = csv_wr
				rq.meta['Constituent'] = Constituent
				rq.meta['month'] = month
				rq.meta['date'] = date
				rq.meta['year'] = year
				rq.meta['revision_num'] = revision_num
				rq.meta['last_rev_num'] = last_rev_num
				rq.meta['timestamp'] = timestamp
				yield rq
						
	def parse_datewise(self, response):
		# open_in_browser(response)
		Reader = response.meta['Reader']
		Datas = response.meta['Datas']
		csv_wr = response.meta['csv_wr']
		last_month = response.meta['last_month']
		last_date = response.meta['last_date']
		Constituent = response.meta['Constituent']
		month = response.meta['month']
		date = response.meta['date']
		year = response.meta['year']
		revision_num = response.meta['revision_num']
		last_rev_num = response.meta['last_rev_num']
		timestamp = response.meta['timestamp']
		if str(Constituent)	in str(Datas):
			if int(last_date) == int(date) and int(last_rev_num) + 1 == int(revision_num):
				print ('\n\nIterating to Current Date Revision Number =>', date, revision_num)
				if 'BRPL' in Constituent:
					rq = scrapy.Request(response.url, callback=self.parse_results)
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['csv_wr'] = csv_wr
					rq.meta['Constituent'] = Constituent
					yield rq
				else:
					rq = scrapy.FormRequest(
						response.url,
							headers={
								'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
								'accept-language': 'en-US,en;q=0.9',
								'cache-control': 'max-age=0',
								'content-type': 'application/x-www-form-urlencoded',
								'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
								'referrerPolicy': 'strict-origin-when-cross-origin',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
								},

							formdata={
								'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
								'__EVENTARGUMENT':'',
								'__LASTFOCUS':'',
								'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
								'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
								'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
								'ctl00$ContentPlaceHolder2$ddmonth':month,
								'ctl00$ContentPlaceHolder2$ddday':date,
								'ctl00$ContentPlaceHolder2$txtyear':year,
								'ctl00$ContentPlaceHolder2$ddrevnon':revision_num,
							}, meta=response.meta, callback=self.parse_results)
					rq.meta['Constituent'] = Constituent
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['csv_wr'] = csv_wr
					yield rq
					
			if last_month < month:
				print ('\n\nStarting a Iteration with Previous Ended Month, Date and TimeStamp\n\n')
				print ('Last Month, Revison Number and Last Ended Date => ', last_month, last_rev_num, last_date, Constituent)
				for previous_month in range(int(last_month), int(month) + 1):
					month = response.xpath('//*[@id="ContentPlaceHolder2_ddmonth"]/option[@selected]/@value').extract_first()
					if int(previous_month) == int(month):
						for previous_date in range(1, int(date) + 1):
							if previous_date < 10:
								previous_date = '0' + str(previous_date)
							print ('Entering to => ', previous_date, last_rev_num, Constituent)
							rq = scrapy.FormRequest(
								response.url,
									headers={
										'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
										'accept-language': 'en-US,en;q=0.9',
										'cache-control': 'max-age=0',
										'content-type': 'application/x-www-form-urlencoded',
										'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
										'referrerPolicy': 'strict-origin-when-cross-origin',
										'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
										},

									formdata={
										'__EVENTTARGET':'ctl00$ContentPlaceHolder2$ddday',
										'__EVENTARGUMENT':'',
										'__LASTFOCUS':'',
										'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
										'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
										'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
										'ctl00$ContentPlaceHolder2$ddmonth':str(month),
										'ctl00$ContentPlaceHolder2$ddday':str(previous_date),
										'ctl00$ContentPlaceHolder2$txtyear':year,
										'ctl00$ContentPlaceHolder2$ddrevnon':'',
									}, meta=response.meta, callback=self.parse_date)
							rq.meta['Reader'] = Reader
							rq.meta['Datas'] = Datas
							rq.meta['Constituent'] = Constituent
							rq.meta['month'] = month
							rq.meta['date'] = date
							rq.meta['year'] = year
							rq.meta['revision_num'] = revision_num
							rq.meta['previous_date'] = previous_date
							rq.meta['last_rev_num'] = last_rev_num
							yield rq
							
					if int(previous_month) != int(month):
						if previous_month < 10:
							month = '0' + str(previous_month)
						if month == '01':
							end_date = '31'
						elif month == '02':
							end_date = '28'
						elif month == '03':
							end_date = '31'
						elif month == '04':
							end_date = '30'
						elif month == '05':
							end_date = '31'
						elif month == '06':
							end_date = '30'
						elif month == '07':
							end_date = '31'
						elif month == '08':
							end_date = '31'
						elif month == '09':
							end_date = '30'
						elif month == '10':
							end_date = '31'
						elif month == '11':
							end_date = '30'
						elif month == '12':
							end_date = '31'
						for previous_date in range(int(last_date), int(end_date) + 1):
							if previous_date < 10:
								previous_date = '0' + str(previous_date)
							print ('Entering to => ', previous_date, last_rev_num, month, Constituent)
							rq = scrapy.FormRequest(
								response.url,
									headers={
										'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
										'accept-language': 'en-US,en;q=0.9',
										'cache-control': 'max-age=0',
										'content-type': 'application/x-www-form-urlencoded',
										'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
										'referrerPolicy': 'strict-origin-when-cross-origin',
										'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
										},

									formdata={
										'__EVENTTARGET':'ctl00$ContentPlaceHolder2$ddday',
										'__EVENTARGUMENT':'',
										'__LASTFOCUS':'',
										'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
										'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
										'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
										'ctl00$ContentPlaceHolder2$ddmonth':str(month),
										'ctl00$ContentPlaceHolder2$ddday':str(previous_date),
										'ctl00$ContentPlaceHolder2$txtyear':year,
										'ctl00$ContentPlaceHolder2$ddrevnon':'',
									}, meta=response.meta, callback=self.parse_date)
							rq.meta['Reader'] = Reader
							rq.meta['Datas'] = Datas
							rq.meta['Constituent'] = Constituent
							rq.meta['month'] = month
							rq.meta['date'] = date
							rq.meta['year'] = year
							rq.meta['revision_num'] = revision_num
							rq.meta['previous_date'] = previous_date
							rq.meta['last_rev_num'] = last_rev_num
							yield rq
							
												
					
			if last_date < date:
				print ('\n\nStarting a Iteration with Previous Ended Date and TimeStamp\n\n')
				print ('Last Revison Number and Last Ended Date => ', last_rev_num, last_date, Constituent)
				for previous_date in range(int(last_date), int(date) + 1):
					if previous_date < 10:
						previous_date = '0' + str(previous_date)
					print ('Entering to => ', previous_date, last_rev_num, Constituent)
					rq = scrapy.FormRequest(
						response.url,
							headers={
								'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
								'accept-language': 'en-US,en;q=0.9',
								'cache-control': 'max-age=0',
								'content-type': 'application/x-www-form-urlencoded',
								'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
								'referrerPolicy': 'strict-origin-when-cross-origin',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
								},

							formdata={
								'__EVENTTARGET':'ctl00$ContentPlaceHolder2$ddday',
								'__EVENTARGUMENT':'',
								'__LASTFOCUS':'',
								'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
								'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
								'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
								'ctl00$ContentPlaceHolder2$ddmonth':month,
								'ctl00$ContentPlaceHolder2$ddday':str(previous_date),
								'ctl00$ContentPlaceHolder2$txtyear':year,
								'ctl00$ContentPlaceHolder2$ddrevnon':'',
							}, meta=response.meta, callback=self.parse_date)
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['Constituent'] = Constituent
					rq.meta['month'] = month
					rq.meta['date'] = date
					rq.meta['year'] = year
					rq.meta['revision_num'] = revision_num
					rq.meta['previous_date'] = previous_date
					rq.meta['last_rev_num'] = last_rev_num
					yield rq
						
			elif last_rev_num < revision_num:
				print ('\n\nStarting a Iteration with Previous Ended TimeStamp\n\n')
				print ('Last Revision Number =>', last_rev_num, Constituent)
				for particular_rev_num in range(int(last_rev_num) - 1, int(revision_num) + 1):
					if particular_rev_num < 10:
						particular_rev_num = '0' + str(particular_rev_num)
					print ('\n\niterating previous revision number for Constituent =>', particular_rev_num, Constituent)
					rq = scrapy.FormRequest(
						response.url,
							headers={
								'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
								'accept-language': 'en-US,en;q=0.9',
								'cache-control': 'max-age=0',
								'content-type': 'application/x-www-form-urlencoded',
								'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
								'referrerPolicy': 'strict-origin-when-cross-origin',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
								},

							formdata={
								'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
								'__EVENTARGUMENT':'',
								'__LASTFOCUS':'',
								'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
								'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
								'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
								'ctl00$ContentPlaceHolder2$ddmonth':month,
								'ctl00$ContentPlaceHolder2$ddday':date,
								'ctl00$ContentPlaceHolder2$txtyear':year,
								'ctl00$ContentPlaceHolder2$ddrevnon':str(particular_rev_num),
							}, meta=response.meta, callback=self.parse_results)
					rq.meta['Reader'] = Reader
					rq.meta['Datas'] = Datas
					rq.meta['csv_wr'] = csv_wr
					rq.meta['Constituent'] = Constituent
					yield rq
						
			else:
				# test_dat = [Constituent, timestamp, revision_num]
				# csv_wr.writerow(test_dat)
				print ('\n\nNo New Items to extract\n\n')
				
	def parse_results(self, response):
		Reader = response.meta['Reader']
		Datas = response.meta['Datas']
		Constituent = response.meta['Constituent']
		csv_wr = response.meta['csv_wr']
		# open_in_browser(response)
		R1 = response.xpath('//span[contains(.,"Revision No")]/following::td[1]/select/option[@selected]/@value').extract_first()
		Rev2 = response.xpath('//span[contains(.,"Issued on")]/following::td[1]/span/text()').extract_first()
		
		R2 = str(Rev2).replace('/','_').replace('-','_').replace('.','_').replace(':','_').replace(' ','_')
		CSV_TITLE = response.xpath('//*[@id="demoTable1"]/tbody/tr/th/text() | //span[contains(.,"Issued on")]/text() | //span[contains(.,"Revision No:")]/text() | //*[@id="ContentPlaceHolder2_Label7"]//text()[normalize-space()]').extract()
		print ('CSV Title Count for Date, revision Number and Constituent =>', len(CSV_TITLE), R2, R1, Constituent)
		
		if len(CSV_TITLE) > 3:
			# if not os.path.exists('ALL_Constituent_Regionwise'):
				# os.makedirs('ALL_Constituent_Regionwise')
				
			# if not os.path.exists('ALL_Constituent'):
				# os.makedirs('ALL_Constituent')
				
			if not os.path.exists(Constituent):
				os.makedirs(Constituent)
				
			# csv_file2 = open('./ALL_Constituent_Regionwise/' + R1 + '_' + Constituent + '_' + R2 + '.csv', "a+", newline='', encoding='utf-8')
			# csv_wr2 = csv.writer(csv_file2, quoting=csv.QUOTE_ALL)
			
			# csv_file3 = open('./ALL_Constituent_Regionwise/' + R1 + '_' + Constituent + '_' + R2 + '.csv', "r", newline='', encoding='utf-8')
			# Reader2 = csv.reader(csv_file3)
			# Datas2 = list(Reader2)
			# if CSV_TITLE[3] not in str(Datas2):
				# csv_wr2.writerow(CSV_TITLE)
				
			csv_file4 = open('./' + Constituent + '/' + R2 + '_' + Constituent + '_' + R1 + '.csv', "a+", newline='', encoding='utf-8')
			csv_wr4 = csv.writer(csv_file4, quoting=csv.QUOTE_ALL)
			
			csv_file5 = open('./' + Constituent + '/' + R2 + '_' + Constituent + '_' + R1 + '.csv', "r", newline='', encoding='utf-8')
			Reader5 = csv.reader(csv_file5)
			Datas5 = list(Reader5)
			if CSV_TITLE[3] not in str(Datas5):
				csv_wr4.writerow(CSV_TITLE)
					
			# csv_file6 = open('./ALL_Constituent/' + Constituent + '.csv', "a+", newline='', encoding='utf-8')
			# csv_wr6 = csv.writer(csv_file6, quoting=csv.QUOTE_ALL)
			
			# csv_file7 = open('./ALL_Constituent/' + Constituent + '.csv', "r", newline='', encoding='utf-8')
			# Reader7 = csv.reader(csv_file7)
			# Datas7 = list(Reader7)
			# if CSV_TITLE[3] not in str(Datas7):
				# csv_wr6.writerow(CSV_TITLE)
		
		
				
			# ResultReader = csv.reader(csvfile)
			# Datas = list(ResultReader)
			
			CSV_TITLE[0] = Constituent
			CSV_TITLE[1] = response.xpath('//span[contains(.,"Issued on")]/following::td[1]/span/text()').extract_first()
			CSV_TITLE[2] = response.xpath('//span[contains(.,"Revision No")]/following::td[1]/select/option[@selected]/@value').extract_first()
			test_dat = [Constituent, Rev2, R1]
			csv_wr.writerow(test_dat)
			for row in Reader:
				if not Constituent == row[Constituent]:
					csv_wr.writerow(test_dat)
			if CSV_TITLE[1] not in str(Datas5):
				for sel in response.xpath('//*[@id="demoTable1"]/tbody/tr/following-sibling::tr[normalize-space()]'):
					i = 3
					while i < len(CSV_TITLE):
						k = i - 2
						CSV_TITLE[i] = "".join(sel.xpath('./td[' + str(k) + ']/text()').extract()).strip()
						i = i + 1
					dat = (CSV_TITLE)
					if Rev2 not in str(Datas5):
						print ('output data saved into Results.csv => ', dat)
						# csv_wr2.writerow(dat)
						csv_wr4.writerow(dat)
						# csv_wr6.writerow(dat)
						
		
	def parse_date(self, response):
		# open_in_browser(response)
		previous_date = response.meta['previous_date']
		Constituent = response.meta['Constituent']
		month = response.meta['month']
		date = response.meta['date']
		year = response.meta['year']
		revision_num = response.meta['revision_num']
		last_rev_num = response.meta['last_rev_num']
		particular_rev = response.xpath('//*[@id="ContentPlaceHolder2_ddrevnon"]/option[1]/@value').extract_first()
		print ('\n\nParticular Date Last Revision Number => ',  previous_date, particular_rev, month)
		
		if int(previous_date) == int(date) and int(last_rev_num) == int(particular_rev) or int(previous_date) == int(date) and int(last_rev_num) > int(particular_rev):
			for full_rev_num in response.xpath('//*[@id="ContentPlaceHolder2_ddrevnon"]/option/@value').extract():
				print ('\n\nIterating to Current Date Revision Numbers =>', date, full_rev_num, Constituent)
				if int(date) == int(previous_date):
					if int(full_rev_num) == int(particular_rev):
						rq = scrapy.FormRequest(
							response.url,
								headers={
									'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
									'accept-language': 'en-US,en;q=0.9',
									'cache-control': 'max-age=0',
									'content-type': 'application/x-www-form-urlencoded',
									'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
									'referrerPolicy': 'strict-origin-when-cross-origin',
									'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
									},

								formdata={
									'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
									'__EVENTARGUMENT':'',
									'__LASTFOCUS':'',
									'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
									'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
									'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
									'ctl00$ContentPlaceHolder2$ddmonth':month,
									'ctl00$ContentPlaceHolder2$ddday':date,
									'ctl00$ContentPlaceHolder2$txtyear':year,
									'ctl00$ContentPlaceHolder2$ddrevnon':'',
								}, meta=response.meta, callback=self.parse_results)
						rq.meta['Constituent'] = Constituent
						yield rq
					else:
						rq = scrapy.FormRequest(
							response.url,
								headers={
									'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
									'accept-language': 'en-US,en;q=0.9',
									'cache-control': 'max-age=0',
									'content-type': 'application/x-www-form-urlencoded',
									'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
									'referrerPolicy': 'strict-origin-when-cross-origin',
									'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
									},

								formdata={
									'__EVENTTARGET':'ctl00$ContentPlaceHolder2$cmbdiscom',
									'__EVENTARGUMENT':'',
									'__LASTFOCUS':'',
									'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
									'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
									'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
									'ctl00$ContentPlaceHolder2$ddmonth':month,
									'ctl00$ContentPlaceHolder2$ddday':date,
									'ctl00$ContentPlaceHolder2$txtyear':year,
									'ctl00$ContentPlaceHolder2$ddrevnon':str(full_rev_num),
								}, meta=response.meta, callback=self.parse_results)
						rq.meta['Constituent'] = Constituent
						yield rq
				
		if int(previous_date) != int(date) or int(last_rev_num) < int(particular_rev):
			print ('\n\nIterating to Previous Date Revision Numbers\n\n')
			for particular_rev_num in range(int(last_rev_num) - 1, int(particular_rev) + 1):
				if (particular_rev_num) == int(particular_rev):
					if particular_rev_num < 10:
						particular_rev_num = '0' + str(particular_rev_num)
					print ('\n\nIterating to Previous Date Exact Revision Number =>', month, particular_rev_num, particular_rev, Constituent)
					rq = scrapy.FormRequest(
						response.url,
							headers={
								'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
								'accept-language': 'en-US,en;q=0.9',
								'cache-control': 'max-age=0',
								'content-type': 'application/x-www-form-urlencoded',
								'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
								'referrerPolicy': 'strict-origin-when-cross-origin',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
								},

							formdata={
								'__EVENTTARGET':'ctl00$ContentPlaceHolder2$ddrevnon',
								'__EVENTARGUMENT':'',
								'__LASTFOCUS':'',
								'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
								'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
								'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
								'ctl00$ContentPlaceHolder2$ddmonth':month,
								'ctl00$ContentPlaceHolder2$ddday':str(previous_date),
								'ctl00$ContentPlaceHolder2$txtyear':year,
								'ctl00$ContentPlaceHolder2$ddrevnon':'',
							}, meta=response.meta, callback=self.parse_results)
					rq.meta['Constituent'] = Constituent
					yield rq
					
				else:
					if int(previous_date) != int(date):
						if particular_rev_num < 10:
							particular_rev_num = '0' + str(particular_rev_num)
						print ('\n\nIterating to particular_rev_num =>', month, previous_date, particular_rev_num, Constituent)
						rq = scrapy.FormRequest(
							response.url,
								headers={
									'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
									'accept-language': 'en-US,en;q=0.9',
									'cache-control': 'max-age=0',
									'content-type': 'application/x-www-form-urlencoded',
									'referrer': 'https://www.delhisldc.org/dswebpage.aspx',
									'referrerPolicy': 'strict-origin-when-cross-origin',
									'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
									},

								formdata={
									'__EVENTTARGET':'ctl00$ContentPlaceHolder2$ddrevnon',
									'__EVENTARGUMENT':'',
									'__LASTFOCUS':'',
									'__VIEWSTATE':response.xpath('//*[@id="__VIEWSTATE"]/@value').extract_first(),
									'__EVENTVALIDATION':response.xpath('//*[@id="__EVENTVALIDATION"]/@value').extract_first(),
									'ctl00$ContentPlaceHolder2$cmbdiscom':Constituent,
									'ctl00$ContentPlaceHolder2$ddmonth':month,
									'ctl00$ContentPlaceHolder2$ddday':str(previous_date),
									'ctl00$ContentPlaceHolder2$txtyear':year,
									'ctl00$ContentPlaceHolder2$ddrevnon':str(particular_rev_num),
								}, meta=response.meta, callback=self.parse_results)
						rq.meta['Constituent'] = Constituent
						yield rq
				
		
			
process = CrawlerProcess(settings=get_project_settings())
scheduler = TwistedScheduler()
scheduler.add_job(process.crawl, 'interval', args=[DelhiSpider], minutes=5)
	
scheduler.start()
process.start(False)