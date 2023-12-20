from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Handphone as handphoneModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'ram': 7, 'memori_internal': 6, 'processor': 8, 'layar': 5, 'harga': 5, 'baterai': 8}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(handphoneModel.id, handphoneModel.nama_handphone, handphoneModel.ram, handphoneModel.memori_internal, handphoneModel.processor, handphoneModel.layar, handphoneModel.harga, handphoneModel.baterai)        
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': Handphone.id, 'nama_handphone': Handphone.nama_handphone, 'ram': Handphone.ram, 'memori_internal': Handphone.memori_internal, 'processor': Handphone.processor, 
                'layar': Handphone.layar, 'harga': Handphone.harga, 'baterai': Handphone.baterai} for Handphone in result]
    @property
    def normalized_data(self):
        ram_values = [data.get('ram', 0) for data in self.data]
        memori_internal_values = [data['memori_internal'] for data in self.data]
        processor_values = [data['processor'] for data in self.data]
        layar_values = [data['layar'] for data in self.data]  
        harga_values = [data['harga'] for data in self.data]
        baterai_values = [data['baterai'] for data in self.data]

        max_ram_value = max(ram_values) if ram_values else 1
        max_memori_internal_value = max(memori_internal_values) if memori_internal_values else 1
        max_processor_value = max(processor_values) if processor_values else 1
        max_layar_value = max(layar_values) if layar_values else 1
        max_harga_value = max(harga_values) if harga_values else 1
        max_baterai_value = max(baterai_values) if baterai_values else 1

        return [
            {
                'id': data['id'],
                'nama_handphone': data['nama_handphone'],
                'harga': data['harga'] / max_harga_value if max_harga_value != 0 else 0,
                'memori_internal': data['memori_internal'] / max_memori_internal_value,
                'processor': data['processor'] / max_processor_value,
                'layar': data['layar'] / max_layar_value,
                'ram': data['ram'] / max_ram_value,
                'baterai': data['baterai'] / max_baterai_value,
            }
            for data in self.data
            ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'id': row['id'],
                'nama_handphone': row['nama_handphone'],
                'produk': row['ram'] ** self.weight['ram'] *
                    row['memori_internal'] ** self.weight['memori_internal'] *
                    row['processor'] ** self.weight['processor'] *
                    row['layar'] ** self.weight['layar'] *
                    row['harga'] ** self.weight['harga'] *
                    row['baterai'] ** self.weight['baterai']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['id'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'Handphone': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'id': row['id'],
                'nama_handphone': row['nama_handphone'],
                'model': row.get('model'),
                'Score': round(row['ram'] * weight['ram'] +
                        row['memori_internal'] * weight['memori_internal'] +
                        row['processor'] * weight['processor'] +
                        row['layar'] * weight['layar'] +
                        row['harga'] * weight['harga'] +
                        row['baterai'] * weight['baterai'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'Handphone': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class Mobil(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(handphoneModel).order_by(handphoneModel.id)
        result_set = query.all()
        data = [{'id': row.id, 'nama_handphone': row.nama_handphone, 'ram': row.ram, 'memori_internal': row.memori_internal, 'processor': row.processor, 'layar': row.layar, 
                'harga': row.harga, 'baterai': row.baterai,}
                for row in result_set]
        return self.get_paginated_result('handphone/', data, request.args), 200

api.add_resource(Mobil, '/handphone')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)