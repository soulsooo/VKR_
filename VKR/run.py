# run.py
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 СЕРВЕР ЗАПУЩЕН (reloader OFF)")
    print("📝 ПЕРЕЗАПУСКАЙТЕ ВРУЧНУЮ ПРИ ИЗМЕНЕНИЯХ!")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)