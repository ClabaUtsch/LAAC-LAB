<?php

namespace Tests\Feature;

use Tests\TestCase;

class ConexaoBancoTest extends TestCase
{
    public function test_conexao_mysql_esta_disponivel(): void
    {
        $this->assertSame('mysql', config('database.connections.mysql.driver'));
    }

    public function test_sqlite_nao_herda_o_nome_do_banco_do_mysql(): void
    {
        $this->assertNotSame(
            config('database.connections.mysql.database'),
            config('database.connections.sqlite.database'),
            'A conexao sqlite nao pode ler DB_DATABASE, senao tenta abrir um arquivo com o nome do banco MySQL.'
        );
    }

    public function test_testes_rodam_em_sqlite_em_memoria(): void
    {
        $this->assertSame('sqlite', config('database.default'));
        $this->assertSame(':memory:', config('database.connections.sqlite.database'));
    }

    /**
     * Sem isto o ON DELETE CASCADE das FKs e silenciosamente ignorado no
     * SQLite. Exigido pela secao 3.1 da spec.
     */
    public function test_sqlite_aplica_as_constraints_de_chave_estrangeira(): void
    {
        $this->assertTrue(config('database.connections.sqlite.foreign_key_constraints'));
    }
}
