# create_db.py
import os
import sys

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Video, Clip

print("🚀 Criando aplicação Flask...")
app = create_app('development')

with app.app_context():
    print("🗑️  Deletando tabelas antigas...")
    db.drop_all()
    
    print("📦 Criando novas tabelas...")
    db.create_all()
    
    print("✅ Tabelas criadas com sucesso!")
    
    # Criar usuário admin
    print("👤 Criando usuário admin...")
    admin = User(
        email="admin@binhocut.com",
        username="admin",
        full_name="Administrador",
        plan="enterprise"
    )
    admin.set_password("admin123")
    
    db.session.add(admin)
    
    # Criar usuário de teste
    print("👤 Criando usuário de teste...")
    test_user = User(
        email="test@test.com",
        username="testuser",
        full_name="Usuário Teste",
        plan="free"
    )
    test_user.set_password("senha123")
    
    db.session.add(test_user)
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ BANCO DE DADOS CONFIGURADO COM SUCESSO!")
    print("="*60)
    print("\n👤 USUÁRIOS CRIADOS:")
    print("\n1. Admin:")
    print("   📧 Email: admin@binhocut.com")
    print("   🔑 Senha: admin123")
    print("\n2. Teste:")
    print("   📧 Email: test@test.com")
    print("   🔑 Senha: senha123")
    print("\n" + "="*60)
    print("\n🚀 Agora execute: python run.py")
    print("🌐 Depois acesse: http://localhost:5000")
    print("="*60 + "\n")