# Database migrations

Convenciona-se que o controle dos schemas das instâncias da aplicação fica sob controle dos mantenedores da solução. Entendemos que o versionamento de uma base de dados não difere de um versionamento de um repositório de código. Portanto, como não automatizamos os `commits` e `pushes`, não automatizamos também as operações realizadas através do `alembic`

## Local

Para executar as migrações da base, usa-se o `alembic`. Para atualizar uma instância do postgres para a mais atual:

```bash
alembic -x data=true upgrade head
```

**Observação**: O argumento `-x data=true` habilita a população de dados *seed*

## Homologação e Produção

Para aplicar as migrações nas instâncias de homologação (`staging`) e produção (`production`), é necessário executar **antes de aplicar** o upgrade ou downgrade:

```bash
source .env-{staging|production}
```

**Observação**: Reconhecemos que é uma falha de vulnerabilidade expor os arquivos `.env` no repositório. Mas como este é um repositório privado e confiamos na segurança fornecida pelo GitHub, não é um problema. Pretendemos usar alguma forma de encriptação destes arquivos no futuro, no entanto.