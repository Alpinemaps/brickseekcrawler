#!/usr/bin/python

from requests_html import HTMLSession
from IPython.display import HTML, display
from os import environ
import pandas as pd
from datetime import datetime
import argparse
import os

# Main URL
BRICKSEEK_URL_WNT = "https://brickseek.com/walmart-inventory-checker"
# SECLTOR OF product title
ITEM_TITLE_SELECTOR = 'h3.bsapi-product-overview__title'
# SECLTOR for the table holding all the information we need
INFORMATION_TABLE_SELECTOR = 'div.bsapi-table.bsapi-table--sticky-labels.bsapi-table--bottom-margin.bsapi-table--inventory-checker-stores'

# SECLTOR for each piece of information
ADDRESS_SELECTOR = 'address'
QUANLITY_SELECTOR = 'span.bsapi-table__cell-quantity'
PRICE_SELECTOR = 'div.bsapi-table__cell-price'

# Trim useless strings
ADDRESS_REPLACE_CHAR = '\nGoogle MapsApple Maps'
QUANLITY_REPLACE_CHAR = 'Quantity: '
PRICE_REPLACE_CHAR = '$'

def requests_html_show(url,method = 'get',payload = {}):
    sess = HTMLSession()
    if method == 'get':
        req = sess.get(url,payload)
    elif method =='post':
        req = sess.post(url,payload)
    else:
        raise ValueError('Unknow method')
    return(sess,req)


class Brickseek_Page(HTMLSession): 
    #get colnumn infromation to a list
    def _get_col_info(self,col_selector,replace_char, datatype = str):
        possible_types = ['int','float','str']
        if datatype.__name__ not in possible_types:
            raise ValueError('Unkown data type, please choose from {}'.format(possible_types))
        return [datatype(i.text.replace(replace_char,"")) for i in self._response.html.find(' '.join([INFORMATION_TABLE_SELECTOR,col_selector]))]    
    
    def _retrieve_price_information(self):
        print('Retrieve Price Information...')
        self.title = self._response.html.find(ITEM_TITLE_SELECTOR,first = True).text
        self._inventory_table = pd.DataFrame({'Address':[i.replace('\n',',') for i in self._get_col_info(ADDRESS_SELECTOR,ADDRESS_REPLACE_CHAR)],
                                              'Quanlity':self._get_col_info(QUANLITY_SELECTOR,QUANLITY_REPLACE_CHAR,int),
                                              'Price': self._get_col_info(PRICE_SELECTOR,PRICE_REPLACE_CHAR,float),
                                              'Time': datetime.now().strftime('%m/%d/%y %I:%m'),
                                              'SKU': self.sku,
                                              'ZIP': self.zipcode,
                                              'Title': self.title,
                                              'Store': self.store,
                                              'Discounted': 'No Limit set' if self.limit ==0 else [_<=self.limit for _ in self._get_col_info(PRICE_SELECTOR,PRICE_REPLACE_CHAR,float)]
                                              
                                             })

    def __init__(self,zipcode,sku,limit=0,store = 'WMT'):
        stores_list = ['WMT']
        if store not in stores_list:
            raise ValueError('Unkown data type, please choose from {}'.format(stores_list))
        self.store = store
        self.zipcode = zipcode
        self.sku = sku
        self.limit = limit
        super(HTMLSession, self).__init__()
        print('HTML sesssion started...')
        payload = {'search_method':'sku','sku':str(sku),'zip':str(zipcode),'sort':'distance'}
        if store == 'WMT':
            self._response = self.post(BRICKSEEK_URL_WNT,payload)
        print('Query was sent...')
        try:
            self._retrieve_price_information()
        except:
            print('Error')
            display(HTML(self._response.text))
        print('Information successfully retrieved...')

    @property
    def response(self):
        return self._response
    

    @property
    def inventory_table(self):
        return self._inventory_table
    
    def __repr__(self):
        return ('Inventory Page:\nStore: {}\nSKU: {}\nZIP: {}\nTitle: {}'.format(self.store,self.sku,self.zipcode,self.title))


    

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-zipcode',action="store",elp = 'Zip code')
    parser.add_argument('-sku',action="store",help='sku of the product')
    parser.add_argument('-store',action="store",default = 'WMT')

    xx = Brickseek_Page(zipcode,sku,store)
    
    if 'results.csv' in os.listdir():
        xx.inventory_table.to_csv('results.csv',mode ='a',index = False)
        print('Results were attached to results.csv file...')
    else:
        xx.inventory_table.to_csv('results.csv',index = False) 
        print('No records were found, setup a new results.csv file...')

