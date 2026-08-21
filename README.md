<p align="center"><a href="https://laravel.com" target="_blank"><img src="https://raw.githubusercontent.com/laravel/art/master/logo-lockup/5%20SVG/2%20CMYK/1%20Full%20Color/laravel-logolockup-cmyk-red.svg" width="400" alt="Laravel Logo"></a></p>

<p align="center">
<a href="https://github.com/laravel/framework/actions"><img src="https://github.com/laravel/framework/workflows/tests/badge.svg" alt="Build Status"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/dt/laravel/framework" alt="Total Downloads"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/v/laravel/framework" alt="Latest Stable Version"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/l/laravel/framework" alt="License"></a>
</p>

## About Laravel

Laravel is a web application framework with expressive, elegant syntax. We believe development must be an enjoyable and creative experience to be truly fulfilling. Laravel takes the pain out of development by easing common tasks used in many web projects, such as:

- [Simple, fast routing engine](https://laravel.com/docs/routing).
- [Powerful dependency injection container](https://laravel.com/docs/container).
- Multiple back-ends for [session](https://laravel.com/docs/session) and [cache](https://laravel.com/docs/cache) storage.
- Expressive, intuitive [database ORM](https://laravel.com/docs/eloquent).
- Database agnostic [schema migrations](https://laravel.com/docs/migrations).
- [Robust background job processing](https://laravel.com/docs/queues).
- [Real-time event broadcasting](https://laravel.com/docs/broadcasting).

Laravel is accessible, powerful, and provides tools required for large, robust applications.

## Learning Laravel

Laravel has the most extensive and thorough [documentation](https://laravel.com/docs) and video tutorial library of all modern web application frameworks, making it a breeze to get started with the framework.

In addition, [Laracasts](https://laracasts.com) contains thousands of video tutorials on a range of topics including Laravel, modern PHP, unit testing, and JavaScript. Boost your skills by digging into our comprehensive video library.

You can also watch bite-sized lessons with real-world projects on [Laravel Learn](https://laravel.com/learn), where you will be guided through building a Laravel application from scratch while learning PHP fundamentals.

## Agentic Development

Laravel's predictable structure and conventions make it ideal for AI coding agents like Claude Code, Cursor, and GitHub Copilot. Install [Laravel Boost](https://laravel.com/docs/ai) to supercharge your AI workflow:

```bash
composer require laravel/boost --dev

php artisan boost:install
```

Boost provides your agent 15+ tools and skills that help agents build Laravel applications while following best practices.

## Contributing

Thank you for considering contributing to the Laravel framework! The contribution guide can be found in the [Laravel documentation](https://laravel.com/docs/contributions).

## Code of Conduct

In order to ensure that the Laravel community is welcoming to all, please review and abide by the [Code of Conduct](https://laravel.com/docs/contributions#code-of-conduct).

## Security Vulnerabilities

If you discover a security vulnerability within Laravel, please send an e-mail to Taylor Otwell via [taylor@laravel.com](mailto:taylor@laravel.com). All security vulnerabilities will be promptly addressed.

## License

The Laravel framework is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).

## LaaC Lab — API

Banco alternável pelo `.env`: `DB_CONNECTION=sqlite` (padrão) ou `mysql`.
Depois de trocar, rode `php artisan migrate:fresh`.

`DB_DATABASE` é exclusiva do MySQL. O SQLite usa a sua própria variável,
`DB_SQLITE_DATABASE`; se ela não estiver definida, o padrão é
`database/database.sqlite`. Isso evita que trocar `DB_CONNECTION` de volta
para `sqlite` continue lendo o nome do banco MySQL.

### Endpoints

Cada recurso expõe os cinco verbos REST:

| Verbo | URI | Ação |
|---|---|---|
| GET | `/api/{recurso}` | lista todos (200) |
| GET | `/api/{recurso}/{id}` | busca um (200 / 404) |
| POST | `/api/{recurso}` | cria (201 / 422) |
| PUT/PATCH | `/api/{recurso}/{id}` | atualiza (200 / 404 / 422) |
| DELETE | `/api/{recurso}/{id}` | remove (204 / 404) |

Recursos disponíveis: `usuarios`, `jogos`, `plataformas`, `jogos_plataformas`,
`biblioteca_usuario`, `avaliacoes`, `curtidas_avaliacoes`.

Os quatro últimos são relacionamentos e exigem os ids dos registros que ligam.
Apagar um registro pai apaga os dependentes em cascata: apagar um jogo remove
seus vínculos de plataforma, suas entradas em bibliotecas e suas avaliações;
apagar uma avaliação remove suas curtidas.

Pares que não podem repetir — `(jogo_id, plataforma_id)`,
`(usuario_id, jogo_id)` na biblioteca e `(avaliacao_id, usuario_id)` nas
curtidas — retornam 422. A nota de uma avaliação vai de 0 a 9.9 e é devolvida
como string com uma casa decimal (`"8.0"`).

Em `usuarios`, a senha é enviada no campo `senha` (texto puro, mínimo de 8
caracteres) e gravada com hash na coluna `senha_hash`, que nunca aparece nas
respostas.

Em `jogos`, `data_lancamento` deve ser enviada no formato `YYYY-MM-DD`
(ex.: `2020-12-10`). Outros formatos são rejeitados com 422 para evitar
ambiguidade entre dia e mês.
