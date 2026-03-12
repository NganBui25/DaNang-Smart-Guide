"""
Script import dữ liệu từ file JSON crawl vào MySQL (thông qua Django ORM).
Sử dụng: python scripts/import_data.py

Lưu ý: Chạy từ thư mục backend/
"""
import os
import sys
import json
import django

# Thêm thư mục backend vào sys.path để Django tìm được settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from places.models import Place, Category
from reviews.models import Image

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FILES = {
    "Cafe": "places_coffee.json",
    "Quán ăn": "places_food.json",
    "Vui chơi": "places_play.json",
}


def run_import():
    total = 0
    for cat_name, filename in FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[!] Không tìm thấy: {filepath}, bỏ qua.")
            continue

        # Tạo hoặc lấy Category
        category, _ = Category.objects.get_or_create(name=cat_name)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n[Import] Đang nhập {len(data)} địa điểm từ '{filename}'...")

        for key, place_data in data.items():
            name = place_data.get("name", "").strip()
            if not name:
                continue

            coords = place_data.get("coordinate", [None, None])
            try:
                lat = float(coords[0]) if coords and coords[0] else None
                lng = float(coords[1]) if coords and len(coords) > 1 and coords[1] else None
            except (ValueError, TypeError):
                lat, lng = None, None

            # Dùng get_or_create tránh duplicate khi chạy lại
            place, created = Place.objects.get_or_create(
                name=name,
                defaults={
                    "address": place_data.get("address", ""),
                    "lat": lat,
                    "lng": lng,
                    "category": category,
                    "status": "APPROVED",         # Dữ liệu mồi đã được chấp nhận
                    "is_hidden_gem": False,
                }
            )

            if not created:
                print(f"  [skip] '{name}' đã tồn tại")
                continue

            # Lưu ảnh (nếu có)
            image_path = place_data.get("image_path")
            if image_path:
                Image.objects.get_or_create(place=place, image_path=image_path)

            total += 1
            print(f"  [+] '{name}'")

    print(f"\n✅ Import hoàn thành! Tổng {total} địa điểm mới được thêm vào database.")


if __name__ == "__main__":
    run_import()
