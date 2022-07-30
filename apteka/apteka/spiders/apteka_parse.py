import scrapy
import time
import datetime

ts = time.time()
datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


class AptekaParseSpider(scrapy.Spider):
    name = 'apteka_parse'
    allowed_domains = ['apteka-ot-sklada.ru']
    start_urls = ['https://apteka-ot-sklada.ru/catalog/sportivnoe-pitanie',
                  'https://apteka-ot-sklada.ru/catalog/letnie-serii']

    def parse(self, response):
        for link in response.css('div.ui-card__preview a::attr(href)'):
            yield response.follow(link, callback=self.parse_item)

        for page in response.css('a.ui-pagination__link::attr(href)'):
            yield response.follow(page, callback=self.parse, cookies={'city': 39})

    def parse_item(self, response):
        url = response.request.url
        name = response.css('h1.text_size_display-1 span::text').get()
        city = response.css('div.layout-city span.ui-link__text::text').get().strip()
        price_current = 0
        delivery = ""
        if response.css('div.goods-offer-panel__price span::text').get() is not None:
            price_current = float(response.css('div.goods-offer-panel__price span::text').get().strip().replace(' ', '').strip('₽'))
            delivery = response.css('li.goods-offer-panel__records-item span.text::text').get()
        else:
            price_current = "Временно нет на складе"
            delivery = "Временно нет на складе"
        price_original = 0
        price_sale_tag = 0
        if response.css('span.goods-offer-panel__cost_old::text').get() is not None:
            price_original = float(
                response.css('span.goods-offer-panel__cost_old::text').get().strip().replace(' ', '').strip('₽'))
            price_sale_tag = float((price_original - price_current) * 100 // price_original)
        else:
            price_original = None
        img = response.css('img.goods-photo::attr(src)').get()
        set_img = response.css('li.goods-gallery__preview-item img::attr(src)').getall()
        stock = False
        stock_count = 0
        if response.css('span.goods-offer-panel__records-label::text').get() is not None:
            stock = True
            stock_count = response.css('li.goods-offer-panel__records-item span.ui-link__text::text').get().split()[2]
        description = response.css('div.ui-collapsed-content__content p::text').getall()
        country = response.css("div.page-header__description span::text").getall()[0]
        delivery = response.css('li.goods-offer-panel__records-item span.text::text').get()

        yield {"timestamp": datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
               "city": city,
               "url": url,
               "title": name,
               "brand": response.css('div.page-header__description span::text').getall()[1],
               "section": response.css('li.ui-breadcrumbs__item span.ui-link__text span::text').getall(),
               "price_data": {"current": price_current, "original": price_original, "sale_tag": f'{price_sale_tag} %'},
               "stock": {
                   "in_stock": stock,
                   "count": stock_count
               },
               "assets": {
                   "main_image": response.urljoin(img),
                   "set_images": list(map(lambda i: response.urljoin(i), set_img)),
               },
               "metadata": {
                   "__description": f' Страна: {country}, '
                                    f' Доставка: {delivery},' + ''.join(description).strip().replace('\r\n\t', '')
                }
               }
