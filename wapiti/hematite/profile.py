
class Profile(object):
    default_headers = []

    def populate_headers(self, request):
        for k, v in self.default_headers:
            field = request._header_field_map.get(k)
            if not field:
                request.headers.add(k, v)
            else:
                field.__set__(request, v)


class HematiteProfile(Profile):  # TODO: naming? DefaultProfile?
    default_headers = [('User-Agent', 'Hematite/0.6'),
                       ('Accept-Encoding', 'gzip')]
