import json

import scrapy
import os
import xmlrpc.client as xrpc

subtitles_path = "/home/burak/Documents/Courses-2016f/CS464/Project/Subtitles"
url_template = "http://www.imdb.com/search/title?genres=%s&explore=genres&sort=num_votes,desc&view=simple"
imdb_page_limit = 1

server = xrpc.ServerProxy("http://api.opensubtitles.org/xml-rpc")
token = server.LogIn("", "", "en", "OSTestUserAgentTemp").get("token")

class SubtitlesSpider(scrapy.Spider):
    name = "subtitles"
    # start_urls = ["http://www.opensubtitles.org/en/search/sublanguageid-all/searchonlymovies-on/genre-action/movielanguage-english/movieimdbratingsign-5/movieimdbrating-7/movieyearsign-5/movieyear-1990/offset-0"]

    start_urls = [ url_template % (genre) for genre in ['action', 'comedy', 'horror', 'war', 'romance', 'adventure']]

    def parse(self, response):
        # return self.parse_movies(response)

        category_name = response.css(".header ::text").extract_first().split(" ")[2]

        folder_path = "%s/%s" % (subtitles_path, category_name)
        try:
            os.mkdir(folder_path, 0o755)
        except OSError:
            print("Directorty cannot be opened in %s" % folder_path)

            import shutil
            shutil.rmtree(folder_path, ignore_errors=True)
        finally:
            os.mkdir(folder_path, 0o755)

        response.meta['page_limit'] = imdb_page_limit # configure # of pages to be visited to 5
        response.meta['category_name'] = category_name
        return self.parse_imdb_movie_ids(response)

    def parse_imdb_movie_ids(self, response):
        next_page_url = response.urljoin(response.css(".next-page").xpath('@href').extract_first())
        category_name = response.meta['category_name']

        # extract imdb id's from collected links. i.e.  http://www.imdb.com/title/tt0468569/?ref_=adv_li_tt
        # then append those ids to current list of ids
        imdb_ids = response.meta.get('imdb_ids', []) + \
                   [ id.split('/')[2][2:] for id in response.css(".col-title a").xpath("@href").extract() ]

        page_limit = response.meta.get('page_limit', 0) - 1 #decrease the page limit for identifying base case
        if page_limit <= 0:
            return self.parse_movies(imdb_ids=imdb_ids, category_name=category_name)

        yield scrapy.Request(url=next_page_url, callback=self.parse_imdb_movie_ids,
                             meta={'imdb_ids': imdb_ids, 'page_limit': page_limit,
                                   'category_name': category_name})

    def parse_movies(self, imdb_ids, category_name):
        # movie_links = response.css(".bnone").xpath('@href').extract()
        # for link in movie_links:
        #     yield scrapy.Request(url=response.urljoin(link), callback=self.parse_movie)
        print("Listing scraped IMDB ids for%s: ", category_name)
        print(imdb_ids)
        impaired_support = True

        subtitles = {} # key => IDSubtitleFile, value => Metadata of subtitle

        # USING IMDB ID'S, DOWNLOAD THEIR METADATA AND SELECT ID OF A SUITABLE SUBTITLE FOR EACH MOVIE
        for imdb_id in imdb_ids[:10]:
            print("Searching subtitle for movie with ID: %s" % imdb_id)
            found_subtitles = server.SearchSubtitles(token, [{'imdbid': imdb_id, 'sublanguageid': 'eng'}])['data']

            if impaired_support:
                impaired_subtitles = list(filter(lambda sub: sub['SubHearingImpaired'] == '1', found_subtitles))

            impaired_label = ""
            if len(impaired_subtitles) > 0:
                subtitle = impaired_subtitles[0]
                impaired_label = "(IMPAIRED)"
            else:
                subtitle = found_subtitles[0] # for now get the first subtitle

            filename = "%s/%s/%s %s" % (subtitles_path, category_name, subtitle['MovieName'], impaired_label)

            subtitles[subtitle['IDSubtitleFile']] = {'imdb_id': imdb_id, 'filename': filename,
                                                     'movie_name': subtitle['MovieName'],
                                                    'SubDownloadLink': subtitle['SubDownloadLink']}

            # with open(filename, 'w') as f:
            #     f.write(json.dumps(subtitle['SubDownloadLink']))
            #     # yield parse_movie(imdb_id)


        #DOWNLOAD SUBTITLES AND WRITE THEM INTO FILES
        print("Downloading subtitles of %s" % category_name)
        subtitle_ids = [ idsubtitlefile for idsubtitlefile, val in subtitles.items()]
        subtitle_files_response = server.DownloadSubtitles(token, subtitle_ids[:1])

        import base64
        import gzip

        if subtitle_files_response['status'] == '200 OK':
            print("Subtitles downloaded, writing to files...")
            for subtitle_object in subtitle_files_response['data']: #each subtitle_object has base64 data and idsubtitlefile key
                sub = subtitles[subtitle_object['idsubtitlefile']]

                with open(sub['filename'], 'w') as file:
                    file.write(gzip.decompress(base64.b64decode(subtitle_object['data'])).decode())
                    print("Subtitle file saved into: %s" % sub['filename'])

    def parse_movie(self):
        pass