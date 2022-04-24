from .base_extractor import BaseExtractor
import re 

class RegexExtractor(BaseExtractor):
    
    def regex_overstock(files):

        for file in files:

            data = []

            title_regex = "<b>(.+-[kK]t[^<]+)</b>"
            list_price_regex = "<b>List Price:</b></td><td align=\"left\" nowrap=\"nowrap\"><s>([^<]+)</s>"
            price_regex = "<span class=\"bigred\"><b>([^<]+)</b></span>"
            saving_regex = "<span class=\"littleorange\">([$][^<]+)</span>"
            content_regex = "<span class=\"normal\">([^<]+)"

            regex = title_regex + "</a><br>[\s]+<table><tbody><tr><td valign=\"top\"><table>[\s]+<tbody><tr><td align=\"right\" nowrap=\"nowrap\">" + \
                    list_price_regex + "</td></tr>[\s]+<tr><td align=\"right\" nowrap=\"nowrap\"><b>Price:</b></td><td align=\"left\" nowrap=\"nowrap\">" + \
                    price_regex + "</td></tr>[\s]+<tr><td align=\"right\" nowrap=\"nowrap\"><b>You Save:</b></td><td align=\"left\" nowrap=\"nowrap\">" + \
                    saving_regex + "</td></tr>[\s]+</tbody></table>[\s]+</td><td valign=\"top\">" + \
                    content_regex

            # print(regex)

            matches = re.finditer(regex, file)

            for match in matches:

                tmp_saving = match.group(4).split()

                data_el = {
                    "title": match.group(1),
                    "list_price": match.group(2),
                    "price": match.group(3),
                    "item_saving": tmp_saving[0],
                    "item_saving_percent": tmp_saving[1].strip("()"),
                    "content": match.group(5).replace("\n", " ")
                }

                data.append(data_el)

            print(data)