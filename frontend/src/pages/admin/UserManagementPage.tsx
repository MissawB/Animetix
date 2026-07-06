import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../features/admin/services/adminService';

import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Shield, UserX, UserCheck, Calendar, Star, Search, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  level: number;
  tier: string;
}

const UserManagementPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = React.useState('');

  const { data: users, isLoading, refetch } = useQuery<AdminUser[]>({
    queryKey: ['admin-users'],
    queryFn: adminService.getUsers,
  });

  const toggleStaffMutation = useMutation({
    mutationFn: adminService.toggleStaff,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: adminService.toggleActive,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const filteredUsers = users?.filter(u => 
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) || 
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-12">
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-16">
            <div>
              <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2">
                USER <span className="text-blue-500">MANAGEMENT</span>
              </h1>
              <p className="text-xs font-black opacity-30 uppercase tracking-[0.3em]">
                {t('admin.users.subtitle', 'Contrôle des accès et permissions du système')}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
               <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    aria-label={t('admin.users.search_aria', 'Rechercher un utilisateur')}
                    placeholder={t('admin.users.search_placeholder', 'Rechercher un utilisateur...')}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/10 rounded-xl pl-12 pr-6 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 w-64 transition-all"
                  />
               </div>
               <Button variant="outline" onClick={() => refetch()} className="p-3">
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
               </Button>
            </div>
          </div>

          <Card padding="none" className="overflow-hidden shadow-2xl border-none">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 dark:bg-black/40 text-[10px] font-black uppercase tracking-widest text-gray-400 border-b border-gray-100 dark:border-white/5">
                    <th className="px-8 py-6">{t('admin.users.th_user', 'Utilisateur')}</th>
                    <th className="px-8 py-6">{t('admin.users.th_status_tier', 'Statut & Tier')}</th>
                    <th className="px-8 py-6 text-center">{t('admin.users.th_level', 'Niveau')}</th>
                    <th className="px-8 py-6">{t('admin.users.th_joined_date', "Date d'inscription")}</th>
                    <th className="px-8 py-6 text-right">{t('common.actions', 'Actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="px-8 py-20 text-center font-black italic opacity-20 uppercase tracking-[0.5em]">
                        {t('admin.users.loading_archives', 'Chargement des archives...')}
                      </td>
                    </tr>
                  ) : filteredUsers?.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-8 py-20 text-center font-black italic opacity-20 uppercase tracking-[0.5em]">
                        {t('admin.users.no_users_found', 'Aucun utilisateur trouvé')}
                      </td>
                    </tr>
                  ) : filteredUsers?.map((user) => (
                    <tr key={user.id} aria-label={`Utilisateur ${user.username}`} className="hover:bg-gray-50/50 dark:hover:bg-white/5 transition-colors group">
                      <td aria-label={`Profil de ${user.username}`} className="px-8 py-6">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black italic text-sm border-2 transform group-hover:rotate-6 transition-transform ${user.is_staff ? 'bg-blue-500/10 border-blue-500 text-blue-500' : 'bg-gray-100 dark:bg-white/5 border-transparent text-gray-400'}`}>
                            {user.username[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-black text-black dark:text-white leading-none mb-1">{user.username}</p>
                            <p className="text-[10px] text-gray-400 font-medium">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <div className="flex flex-wrap gap-2">
                          {user.is_staff && (
                            <Badge variant="primary" className="bg-blue-600/20 text-blue-500 border-blue-500/30">
                              <Shield className="w-3 h-3" /> Admin
                            </Badge>
                          )}
                          <Badge variant="neutral" className="bg-yellow-400/20 text-yellow-600 dark:text-yellow-400 border-yellow-400/30">
                             <Star className="w-3 h-3 fill-current" /> {user.tier.toUpperCase()}
                          </Badge>
                          {!user.is_active && (
                            <Badge variant="danger" className="bg-red-500/20 text-red-500 border-red-500/30">
                              {t('admin.users.banned', 'Banni')}
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-8 py-6 text-center">
                        <span className="font-black italic manga-font text-lg text-black dark:text-white">
                          Lvl.{user.level}
                        </span>
                      </td>
                      <td className="px-8 py-6">
                        <div className="flex items-center gap-2 text-gray-400 text-xs font-medium">
                          <Calendar className="w-3 h-3" />
                          {new Date(user.date_joined).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-8 py-6 text-right">
                        <div className="flex justify-end gap-2">
                           <button
                             onClick={() => toggleStaffMutation.mutate(user.id)}
                             disabled={toggleStaffMutation.isPending}
                             title={user.is_staff ? t('admin.users.remove_admin', 'Retirer les droits Admin') : t('admin.users.give_admin', 'Donner les droits Admin')}
                             aria-label={user.is_staff ? t('admin.users.remove_admin', 'Retirer les droits Admin') : t('admin.users.give_admin', 'Donner les droits Admin')}
                             className={`p-2 rounded-lg border-2 transition-all ${user.is_staff ? 'border-blue-500/20 bg-blue-500/10 text-blue-500 hover:bg-blue-500 hover:text-white' : 'border-gray-100 dark:border-white/5 text-gray-400 hover:border-blue-500/50 hover:text-blue-500'}`}
                           >
                              <Shield className="w-4 h-4" />
                           </button>
                           <button
                             onClick={() => toggleActiveMutation.mutate(user.id)}
                             disabled={toggleActiveMutation.isPending}
                             title={user.is_active ? t('admin.users.deactivate_account', 'Désactiver le compte') : t('admin.users.reactivate_account', 'Réactiver le compte')}
                             aria-label={user.is_active ? t('admin.users.deactivate_account', 'Désactiver le compte') : t('admin.users.reactivate_account', 'Réactiver le compte')}
                             className={`p-2 rounded-lg border-2 transition-all ${!user.is_active ? 'border-red-500/20 bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white' : 'border-gray-100 dark:border-white/5 text-gray-400 hover:border-red-500/50 hover:text-red-500'}`}
                           >
                              {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                           </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="mt-8 flex justify-center">
             <div className="bg-white dark:bg-[#0f0f1a] p-4 rounded-2xl shadow-lg border border-gray-100 dark:border-white/5 flex gap-4 text-[10px] font-black uppercase tracking-widest text-gray-400">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div> {t('admin.users.legend_admin', 'Administrateur')}
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-400"></div> {t('admin.users.legend_premium', 'Utilisateur Premium')}
                </div>
                <div className="flex items-center gap-2 text-red-500">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div> {t('admin.users.legend_deactivated', 'Compte Désactivé')}
                </div>
             </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default UserManagementPage;
