# Regras para Publicação no Repositório Público

Antes de executar `git subtree push --prefix=backend public main`, verificar e corrigir
os itens abaixo. O repositório público (`mapa-psiquico-engine`) é AGPL e acessível a qualquer pessoa.

---

## O que NUNCA deve aparecer no código público

### Dados pessoais
- Emails reais (ex: `@gmail.com`, `@hotmail.com`)
- Nomes reais do desenvolvedor ou clientes
- Usernames de redes sociais ou plataformas

### Dados de localização reveladores
- Cidade, estado ou país real do desenvolvedor como exemplo hardcoded
- Coordenadas geográficas reais do desenvolvedor (lat/lon)
- Timezones específicos do desenvolvedor em exemplos inline (ex: `"America/Sao_Paulo"`)
- Usar sempre exemplos neutros: `"Europe/London"`, `"America/New_York"`, `"Asia/Tokyo"`

### Dados de negócio
- Nomes internos de features não lançadas
- Estrutura de precificação ou planos
- Nomes de clientes ou casos de uso específicos
- Referências a parcerias ou integrações não públicas

### Credenciais e configuração
- Chaves de API, tokens, senhas (mesmo de desenvolvimento)
- URLs de ambientes internos (staging, admin)
- Nomes de bancos de dados ou schemas de produção

---

## Checklist antes do push público

```
[ ] Nenhum email real no código ou comentários
[ ] Exemplos geográficos usam cidades neutras (Londres, Tóquio, Nova York)
[ ] Nenhuma credencial ou chave de API hardcoded
[ ] .env.example usa apenas placeholders genéricos
[ ] Nenhuma referência a features ou planos não públicos
[ ] Nenhum dado de cliente real em testes ou fixtures
```

## Como verificar rapidamente

```bash
# Buscar emails
grep -r "@gmail\|@hotmail\|@outlook" backend/

# Buscar referências geográficas pessoais
grep -r "Sao_Paulo\|sao paulo\|brunothethe" backend/

# Buscar credenciais
grep -r "password\|secret\|api_key\|token" backend/ --include="*.py"
```

---

## Cidades neutras recomendadas para exemplos

| Cidade | Timezone | Lat | Lon |
|--------|----------|-----|-----|
| Londres | `Europe/London` | 51.5074 | -0.1278 |
| Nova York | `America/New_York` | 40.7128 | -74.0060 |
| Tóquio | `Asia/Tokyo` | 35.6762 | 139.6503 |
| UTC genérico | `UTC` | — | — |

---

## Comando de sincronização

```bash
git subtree push --prefix=backend public main
```

Executar **antes de cada deploy em produção**, não necessariamente a cada commit.
