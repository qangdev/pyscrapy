import re
import scrapy


class TherapistsSpider(scrapy.Spider):
    name = "therapists"
    start_urls = [
        'https://www.emdria.org/directory/'
    ]

    def parse(self, response):
        counter = 0
        for row in response.css('div.fl-post-feed-post'):
            counter += 1

            person_info = row.css('div.directory-listing-details')
            contact_info = row.css('div.directory-listing-contact')

            ''' 
            clean and structure data before return them
            '''
            first_name, mid_name, last_name = "N/A", "N/A", "N/A"
            fullname = person_info.css('a.name').css('span[itemprop="name"]::text').get("N/A").strip()
            if fullname and fullname != "N/A":
                # try simple first by break by whitespace
                name_parts = fullname.split(" ")
                if len(name_parts) == 1:
                    first_name = name_parts.pop()
                elif len(name_parts) == 2:
                    first_name, last_name = name_parts
                else:
                    first_name, mid_name, last_name = name_parts[0], name_parts[1], name_parts[2]                    
            
            # Abbreviations resources
            # - Unit: https://www.apartmentlist.com/renter-life/apartment-address-format
            # - Street: http://trafficsignstore.com/abbreviations.html
            # APT|BLDG|FL|STE|RM|DEPT|UNIT|Apartment|Building|Floor|Suite|Room|Department
            
            unit_pattern = '((APT|BLDG|FL|STE|RM|DEPT|UNIT|Apartment|Building|Floor|Suite|Room|Department)[\s][\d\w\s]*)'
            city_pattern = '(([\w\s\s]+)[,])'
            state_pattern = '[\s]([A-Z]{2})[\s]'
            zipcode_pattern = '([\d]+[-]*[\d]*)'

            addr_street, addr_unit, addr_city, addr_state, addr_zipcode = "N/A", "N/A", "N/A", "N/A", "N/A"
            full_address = contact_info.css('div.ycd-address').css('div.address::text').getall()
            if full_address:
                # There might be 3 lines (3 <br/> tags)
                # THe first and second are stree address + unit
                # The last tag is always City + State + Zip Code
                addr_1, addr_2 = "", ""
                if len(full_address) == 2:
                    addr_1 = full_address[0]
                    addr_2 = full_address[1]
                elif len(full_address) == 3:
                    addr_1 = full_address[0] + " " + full_address[1]
                    addr_2 = full_address[2]

                addr_1, addr_2 = addr_1.strip(), addr_2.strip()

                addr_street = re.sub(unit_pattern, '', addr_1, flags=re.IGNORECASE)
                search_unit = re.search(unit_pattern, addr_1, re.IGNORECASE)
                if search_unit:
                    addr_unit = search_unit.group(1)

                search_city = re.search(city_pattern, addr_2, re.IGNORECASE)
                search_state = re.search(state_pattern, addr_2)
                search_zipcode = re.search(zipcode_pattern, addr_2, re.IGNORECASE)
                if search_city:
                    addr_city = search_city.group(2)
                if search_state:
                    addr_state = search_state.group(1)
                if search_zipcode:
                    addr_zipcode = search_zipcode.group(1)

                addr_street, addr_unit, addr_city, addr_state, addr_zipcode= addr_street.strip(), addr_unit.strip(), addr_city.strip(), addr_state.strip(), addr_zipcode
            license = person_info.css('span.certified-therapist::text').get("N/A")
            if license:
                license = license.strip()

            # Phone number
            phone_number = contact_info.css('div.ycd-phone-number').css('a::text').get("N/A")
            
            if phone_number and phone_number != "N/A":
                phone_number = phone_number.strip()
            

            yield {
                'index': counter,
                'fullname': fullname,
                'first_name': first_name,
                'mid_name': mid_name,
                'last_name': last_name,
                'license': license,
                'specialty': person_info.css('div.ycd-connected-organization::text').get("N/A").strip(),
                'email': contact_info.css('button.action-email::attr(data-ycd-individual-email)').get("N/A").strip(),
                'phone': phone_number,
                'full_address': full_address,
                'address': addr_street,
                'unit': addr_unit,
                'city': addr_city,
                'state': addr_state,
                'zip_code': addr_zipcode
            }