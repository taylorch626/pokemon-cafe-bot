#!/usr/bin/env bash

# pip3 install selenium
# pip3 install webdriver-manager

import argparse
import schedule
import sys
import time
from typing import List

# from itertools import cycle
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

_DEFAULT_WAIT_TIME = 5

_KNOWN_INEFFECTIVE_PROXIES = set([
    '18.116.64.177:8888',
    '47.252.29.28:11222',
    '47.251.43.115:33333',
    '52.226.125.25:8080',
    '68.183.149.126:11010',
    '148.72.140.24:30127',
    '148.72.165.7:30127',
])  # manually add proxies here as needed that never work (e.g. slow to load, never load, etc.)

class SnagBooking:
    def __init__(
        self,
        day_of_month: int,
        num_of_guests: int,
        url: str = 'https://reserve.pokemon-cafe.jp/',
        max_attempts: int = 10):
        
        self._day_of_month = day_of_month
        self._num_of_guests = num_of_guests
        self._url = url
        self._max_attempts = max_attempts
        self.n_attempts = 0
        self.skip_blocks = False

    def setup_driver(self, use_proxy: bool = False):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('detach', True)
        if use_proxy:
            if not hasattr(self, 'proxy_pool'):
                self.generate_proxies()
            # curr_proxy = next(self.proxy_pool)
            if self.proxy_pool:
                curr_proxy = self.proxy_pool.pop()
                print(f'using the next available proxy: {curr_proxy}')
                options.add_argument(f'--proxy-server={curr_proxy}')
            else:
                print('No more valid proxies in pool. Retrying native IP before refreshing pool')
                del self.proxy_pool
            self.n_attempts = 0  # reset the counter
            # curr_proxy = '35.185.196.38:3128'  # a good one that's worked in the past
        self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
    def load_root_url(self):
        try:
            self._driver.get(self._url)
            self._wait = WebDriverWait(self._driver, _DEFAULT_WAIT_TIME)  # set wait condition for up to X seconds for page elements to load
        except WebDriverException:
            print('Bad proxy / internet connection. Retrying...')
            self.setup_driver(use_proxy=True)
            self.snag_booking()
        
    def shutdown_driver(self):
        self._driver.close()
        
    def advance_page_1(self):
        # Agree to T&C and advance to reservation page
        try:
            agree_checkbox = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='agreeChecked']")))
            agree_checkbox.click()
            # print('T&C button clicked')
    
            advance_page_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='button']")))
            advance_page_button.click()
            # print('Advanced to next page')
        except TimeoutException:
            print('Timed out. Starting over...')
            self.snag_booking()
            
        
    def advance_page_2(self):
        # Proceed through next page
        try:
            make_reservation_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='button arrow-down']")))
            make_reservation_button.click()
            # print("'Make a reservation' button clicked")
        except TimeoutException:
            print('Timed out. Starting over...')
            self.snag_booking()
        
    def pick_guests_and_date(self):
        try:
            # Select guest number from drop-down
            guest_dropdown = self._wait.until(EC.presence_of_element_located((By.NAME, 'guest')))
            select = Select(guest_dropdown)
            select.select_by_index(self._num_of_guests)
            # print(f"Selected {self._num_of_guests} guests")
            
            # Move to next month on calendar
            next_month_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '次の月を見る')]")))
            next_month_button.click()
            # print("'Next month' button clicked")
        
            # Click user's requested date and attempt advance to next page
            day_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{self._day_of_month}')]")))
            day_button.click()
            # print(f"Day {self._day_of_month} selected")
            
        except TimeoutException:
            print('Timed out. Starting over...')
            self.snag_booking()
            
    def click_on_time(self):
        try:
            advance_page_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='button']")))
            advance_page_button.click()
            # print('Advanced to next page')
        except TimeoutException:
            while '(Reloading)' in driver.page_source:
                self.reload_congested_page()
            
    def reload_congested_page(self):
        reload_button = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='button arrow-down']")))
        reload_button.click()
        
    def book_if_available(self):
        try:
            # ~TODO~: update the contains in the xpath to be not(contains(...))
            # good_times = self._driver.find_elements(By.XPATH, "//*[@class='status-box']/div[last()][contains(text(), 'Full')]/ancestor::*[self::div[@class='time-cell']]")
            good_times = self._driver.find_elements(By.XPATH, "//*[@class='status-box']/div[last()][not(contains(text(), 'Full'))]/ancestor::*[self::div[@class='time-cell']]")  # THIS IS THE OFFICIAL ONE
            # try to click around the middle of the list, if any matches
            if good_times:
                # attempt to click on a match
                good_times[len(good_times) // 2].click()
                print('Got an opening!')
            else:
                print('All times taken. Starting over...')
                self.snag_booking()
        except TimeoutException:
            print('Timed out. Starting over...')
            self.snag_booking()
            
    def generate_proxies(self):
        if not hasattr(self, '_driver'):  # use native IP to get first list
            self.setup_driver(use_proxy=False)
        proxy_url = 'https://www.us-proxy.org/'
        self._driver.get(proxy_url)
        
        if not hasattr(self, '_wait'):
            self._wait = WebDriverWait(self._driver, _DEFAULT_WAIT_TIME)  # set wait condition for up to X seconds for page elements to load
        table_load_check = self._wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'fpl-list')]")))
        
        # select only rows with https as 'yes'; http is insecure and unreliable
        https_rows = self._driver.find_elements(By.XPATH, "//*[contains(text(), 'yes') and contains(@class, 'hx')]/ancestor::*[self::tr]")
        if https_rows:
            proxy_list = []
            for row in https_rows:
                row_info = row.find_elements(By.XPATH, ".//td")
                potential_proxy = ':'.join([row_info[0].text, row_info[1].text])
                if potential_proxy not in _KNOWN_INEFFECTIVE_PROXIES:
                    proxy_list.append(potential_proxy)
            if not proxy_list:
                raise ValueError('No valid https proxies available! Relaunch script to attempt from scratch.')
            proxy_set = set(proxy_list)
            print(f'found some fresh proxies: {proxy_set}')
            self.proxy_pool = proxy_set
            # self.proxy_pool = cycle(proxy_set)
            return
        raise ValueError('No valid https proxies available! Relaunch script to attempt from scratch.')
            
    def snag_booking(self):
        self.n_attempts += 1
        print(self.n_attempts)
        if self.n_attempts >= self._max_attempts:
            print('Max attempts reached.')
            sys.exit()
        else:
            if not self.skip_blocks:
                if not hasattr(self, '_driver'):
                    self.setup_driver(use_proxy=False)
                
                self.load_root_url()
                # check if page loaded (especially for proxies)
                if (self._driver.title != '席の予約'):
                    if self._driver.title == '403 Forbidden':
                        print('Bot detected! Rotate!')
                    else:
                        print('Bad proxy / internet connection. Retrying...')
                    self.setup_driver(use_proxy=True)
                    self.load_root_url()
                if self._driver.current_url != self._url:
                    # haven't actually encountered this in practice yet, but could be an edge case.
                    print(f'Loaded url: {self._driver.current_url}')
                    print(f'Page title: {self._driver.title}')
                    print('Encountered server error when loading root url. Starting over...')
                    time.sleep(2)
                    # self.snag_booking()
                
                self.advance_page_1()
                if self._driver.current_url != self._url + 'reserve/auth_confirm':
                    print('Encountered server overload when loading auth_confirm page. Starting over...')
                    self.snag_booking()
                
                self.advance_page_2()
                if self._driver.current_url != self._url + 'reserve/step1':
                    print('Encountered server overload when loading step1 page. Starting over...')
                    self.snag_booking()
                
                self.pick_guests_and_date()
            if datetime.now().strftime('%H:%M') >= '02:00':
                self.skip_blocks = False
                self.click_on_time()
                if self._driver.current_url != self._url + 'reserve/step2':
                    print('Encountered server overload or no availability when loading step2 page. Starting over...')
                    self.snag_booking()
                try:
                    page_load_check = self._wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='time-cell']")))
                except TimeoutException:
                    print('Timed out. Starting over...')
                    self.snag_booking()
                
                self.book_if_available()
                time.sleep(_DEFAULT_WAIT_TIME) # wait for as-yet-unknown subsequent page to load
                if self._driver.current_url in [self._url + suffix for suffix in ['', 'reserve/auth_confirm', 'reserve/step1', 'reserve/step2']]:
                    print('Opening was no good. Starting over...')
                    self.snag_booking()
            else:
                print('Too early')
                self.n_attempts -= 1
                time.sleep(1)
                self.skip_blocks = True
                self.snag_booking()
                
def main(argv: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--day_of_month',
        help='Day of subsequent month for which to attempt booking.',
        default=None,
        type=int,
        required=True,
    )
    parser.add_argument(
        '--num_of_guests',
        help='Number of guests to attempt seating for.',
        default=None,
        type=int,
        required=True,
    )
    parser.add_argument(
        '--max_attempts',
        help="Maximum number of attempts per IP address. If this maxes out, you'll need to rerun the script.",
        default=None,
        type=int,
    )
    
    args, _ = parser.parse_known_args(argv)
    lets_go = SnagBooking(day_of_month=args.day_of_month,
                          num_of_guests=args.num_of_guests,
                          max_attempts=args.max_attempts,
              )
    lets_go.snag_booking()
    
if __name__ == '__main__':
    main(sys.argv)

# lets_go = SnagBooking(day_of_month=8, num_of_guests=4, max_attempts=50)  # TODO: use sys.argv instead of hard-coding and resaving
# lets_go.snag_booking()
# lets_go.shutdown_driver()

# TODO: notes for actual use case: update day_of_month=8, max_attempts (VERY HIGH), and not(contains(...))
