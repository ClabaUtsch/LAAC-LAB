<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

class RoleSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
         // Roles
        $admin  = Role::create(['name' => 'admin',  'guard_name' => 'web']);
        $editor = Role::create(['name' => 'editor', 'guard_name' => 'web']);
        $user   = Role::create(['name' => 'user',   'guard_name' => 'web']);

        // Permissões
        $permissions = [
            'users.view', 'users.create', 'users.edit', 'users.delete',
            'plans.view', 'plans.create', 'plans.edit', 'plans.delete',
            'files.upload', 'files.delete',
        ];

        foreach ($permissions as $perm) {
            Permission::create(['name' => $perm, 'guard_name' => 'web']);
        }

        // Admin tem tudo
        $admin->givePermissionTo(Permission::all());

        // Editor tem permissões limitadas
        $editor->givePermissionTo(['users.view', 'plans.view', 'files.upload']);

        // User básico
        $user->givePermissionTo(['files.upload']);
    }
    }

