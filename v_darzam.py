import os
import requests
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import urllib.request


www = "https://veikalsdarzam.lv/seklas"
# HTML = "https://veikalsdarzam.lv/seklas/darzenu-seklas/raceni/?precu-zime=organic-way"
HTML = input("Ievadiet linku: ")
want_pitures = input("Bildes vajag y/n?")
pages_list = [HTML]
links_list = []
items_list = []


def pagination(first_page):
    r = requests.get(first_page, headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        "accept-language": "en-US,en;q=0.9,lv;q=0.8,ru;q=0.7"
    })
    if r.status_code == 200:
        print("Status: " + str(r.status_code) + ". Web ok")
        soup = BeautifulSoup(r.text, features="lxml")
        page = soup.find("div", id="pagination").find('ul', class_="plist-pagination pagination")  # Ищет пагинация
        if page is None:
            return None
        else:
            next_page = soup.find("div", id="pagination").find("li",
                                                               class_="disabled pagination_next")  # ищет "disabled next page"
            if next_page is None:
                link = soup.find("div", id="pagination").find("li", class_="pagination_next").find('a').get(
                    'href')  # ссылка на следующую страницу
                next_page_link = "{www}{link}".format(www=www, link=link)  # правильно оформляем новую ссылку
                print(f"Skaitam lapas: {next_page_link}")
                pages_list.append(next_page_link)
                sleep(0.1)
                pagination(next_page_link)  # запускаем заново с новой ссылкой
            else:
                return
    else:
        print("Can`t get good response")


def product_link(pages_list):
    for page in pages_list:
        r = requests.get(page, headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "accept-language": "en-US,en;q=0.9,lv;q=0.8,ru;q=0.7",
        })
        soup = BeautifulSoup(r.text, features="lxml")
        products_link = soup.findAll('a', class_="product-name")
        print("Meklējam preču url:")
        for index, product in enumerate(products_link):  # Находим и сохраняем все ссылки с одной страницы в список
            print(f"{index + 1}: {product['title']}")
            links_list.append(product["href"])


def item_content(links_list):
    for index, link in enumerate(links_list):
        print(f"Notiek parsing: {index + 1} ({link})")
        r = requests.get(link, headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "accept-language": "en-US,en;q=0.9,lv;q=0.8,ru;q=0.7",
        })
        soup = BeautifulSoup(r.text, features="lxml")
        # print(soup.prettify)
        
        try:
            item_name = soup.find("h1", class_="bold-product-title").text
        except AttributeError:
            print(f"{index + 1}: Nav nosaukuma {link}")
            item_name = "NAV"

        try:
            item_ean = soup.find("span", class_="product-ean13").next.next.text
        except AttributeError:
            print(f"{index + 1}: Nav svītrkoda {link}")
            item_ean = "NAV"
        
        try:
            item_price = soup.find("span", id="our_price_display").next.replace(" €","")
        except AttributeError:
            print(f"{index + 1}: Nav cenas {link}")
            item_price = "NAV"
        
        try:
            item_info = soup.find("div", class_="rte").find("p").text
        except:
            print(f"{index + 1}: Nav apraksta {link}")
            item_info = "NAV"
        
        try:
            more_info = [(key.text, value.text) for (key, value) in
                             soup.find("table", class_="table-data-sheet").findAll("tr")]
        except AttributeError:
            print(f"{index + 1}: Trūkst informācijas {link}")
            more_info = "NAV"
            
        try:
            item_link_picture = soup.find("div", class_="col-xs-12 col-sm-3").find("a").get("href")
            item_link_picture = item_link_picture.replace("-thickbox_default", "")
        except:
            print(f"{index + 1}: Nav bilžu {link}")
            item_link_picture = "NAV"
        
        more_info_together = (', '.join(str(i) for i in [f"{i}: {v}" for i, v in more_info]))
        
        items_list.append({
            "Nosaukums": item_name,
            "Svītrkods": item_ean,
            "Cena": item_price,
            "Apraksts": str(item_info).strip().replace("<span>", "").replace("</span>", ""),
            "Papildinformācija": more_info_together,
            "Url": link,
            "Bildes": item_link_picture,
        })
    sleep(0.1)


def save_file(items):
    df = pd.DataFrame(items)
    df.to_excel("veikalsdarzam.xlsx", engine='xlsxwriter', index=False)


def save_pictures(items_list):
    FOLDER_name = "/pictures_vd/"
    try:
        for count, item in enumerate(items_list):
            pictures_name = os.getcwd() + FOLDER_name + item["Svītrkods"] + item["Bildes"][-4:]
            os.makedirs(os.path.dirname(pictures_name), exist_ok=True)
            imagefile = open(pictures_name, "wb")
            imagefile.write(urllib.request.urlopen(item["Bildes"]).read())
            imagefile.close()
            print(
                "{text} {number} {nosaukums}".format(text="Picture", number=str(count+1) + ": ", nosaukums=item["Nosaukums"]))
            sleep(0.1)
    except:
        print("Can`t save picture")

pagination(HTML)
product_link(pages_list)
item_content(links_list)
save_file(items_list)
if want_pitures == "y":
    save_pictures(items_list)
else:
    print("Bildes nesaglabājam.")