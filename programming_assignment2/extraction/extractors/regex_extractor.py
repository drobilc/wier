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

    def regex_rtvslo(files):

        data = {}

        for file in files:

            title_regex = r"<h1>([^<]+)</h1>[\s]+<div class=\"subtitle\">([^<]+)</div>[\s]+<div class=\"article-meta-mobile\">[\s]+"
            author_regex = r"<div class=\"author-timestamp\">[\s]+<strong>([^<]+)</strong>([^<]+)</div>"
            lead_regex = r"<p class=\"lead\">([^<]+)</p>"
            content_regex = r"<\/div>[\s]*?<\/figure>[\s]*?<p([\s\S]*?)<div class=\"gallery\">"
            regex = title_regex + author_regex + r"[\s\S]*" + lead_regex + r"[\s\S]*" + content_regex

            matches = re.finditer(regex, file)

            final_content = []

            for match in matches:

                content_text = re.findall(">([^<]+)", match.group(6))
                for text in content_text:
                    if text.startswith('Foto: ') or text.isspace() or text == '2':
                        pass
                    elif text.endswith("CO"):
                        text = text + '2'
                        final_content.append(text)
                    else:
                        final_content.append(text)

                final_content = (' '.join(final_content))

                data = {
                    "author": match.group(3),
                    "published_time": match.group(4).strip('| ').replace("\n", "").replace("\t", ""),
                    "title": match.group(1),
                    "subtitle": match.group(2),
                    "lead": match.group(5),
                    "content": final_content
                }

            print(data)


    def regex_avtonet(files):

        for file in files:

            data = []

            link_regex = "<a class=\"stretched-link\" href=\"([^\"]+)\"></a>"
            title_regex = "<div class=\"GO-Results-Naziv [^\"]+\">[\s]+<span>([^<]+)<\/span>[\s]+</div>"
            data_regex = "<tbody>[\s]*<tr>[\s]+<td class=\"w-25 d-none d-md-block pl-3\">[^<]+</td>[\s]+<td class=\"w-75 pl-3\">([^<]+)" \
                        "</td>[\s]+</tr>(<tr>[\s]+<td class=\"d-none d-md-block pl-3\">[^<]+</td>[\s]+<td class=\"pl-3\">([^<]+)</td>[\s]+" \
                        "</tr>)?<tr>[\s]+<td class=\"d-none d-md-block pl-3\">Gorivo</td>[\s]+<td class=\"pl-3\">([^<]+)</td>[\s]+</tr><tr>[\s]+" \
                        "<td class=\"d-none d-md-block pl-3\">Menjalnik</td>[\s]+<td class=\"pl-3 text-truncate\">([^<]+)</td>[\s]+" \
                        "</tr><tr class=\"d-none d-md-table-row\">[\s]+<td class=\"d-none d-md-block pl-3\">Motor</td>[\s]+<td class=\"pl-3 text-truncate\">[\s]+" \
                        "([^<]+)</td>[\s]+</tr>[\s]+</tbody>[\s]+</table>"

            price_regex = "<div class=\"GO-Results-(Top-)?Price-TXT-[^BbSsTt\"]*\">([^<]+)</div>"

            title_matches = re.findall(title_regex, file)
            link_matches = re.findall(link_regex, file)
            data_matches = re.findall(data_regex, file)
            price_matches = re.findall(price_regex, file)

            # print(link_matches)

            for title in title_matches:
                data_el = {
                    "title": title,
                    "first_registration": "",
                    "kilometers": "",
                    "fuel": "",
                    "gearbox": "",
                    "engine": "",
                    "price": "",
                    "link": ""
                }
                data.append(data_el)

            count = 0
            for link in link_matches:
                data[count]['link'] = link.replace('amp;', '')
                count += 1

            count = 0
            for info in data_matches:
                data[count]['first_registration'] = str(info[0])
                data[count]['kilometers'] = info[2]
                data[count]['fuel'] = info[3]
                data[count]['gearbox'] = info[4]
                data[count]['engine'] = info[5].strip()
                count += 1

            price_matches = price_matches[0::2]
            count = 0
            for price in price_matches:
                data[count]['price'] = price[1]
                count += 1

            print(data)