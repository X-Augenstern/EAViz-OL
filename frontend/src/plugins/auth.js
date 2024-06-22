import useUserStore from '@/store/modules/user'

/**
 * 检查用户是否有完全权限或者具体给定的权限
 */
function authPermission(permission) {
  const all_permission = "*:*:*";  // 全权限字符串
  const permissions = useUserStore().permissions  // 当前用户的权限列表，是一个包含多个权限字符串的数组
  if (permission && permission.length > 0) {  // 非空且长度大于0
    return permissions.some(v => {  // 如果任一条件满足，则 some 方法返回 true，表示用户有所需权限
      return all_permission === v || v === permission
    })
  } else {
    return false
  }
}

/**
 * 检查用户是否是超级管理员或者具体给定的角色
 */
function authRole(role) {
  const super_admin = "admin";
  const roles = useUserStore().roles
  if (role && role.length > 0) {
    return roles.some(v => {
      return super_admin === v || v === role
    })
  } else {
    return false
  }
}

export default {
  // 验证用户是否具备某权限
  hasPermi(permission) {
    return authPermission(permission);
  },

  // 验证用户是否含有指定权限，只需包含其中一个
  hasPermiOr(permissions) {
    return permissions.some(item => {
      return authPermission(item)
    })
  },

  // 验证用户是否含有指定权限，必须全部拥有
  hasPermiAnd(permissions) {
    return permissions.every(item => {
      return authPermission(item)
    })
  },

  // 验证用户是否具备某角色
  hasRole(role) {
    return authRole(role);
  },

  // 验证用户是否含有指定角色，只需包含其中一个
  hasRoleOr(roles) {
    return roles.some(item => {
      return authRole(item)
    })
  },

  // 验证用户是否含有指定角色，必须全部拥有
  hasRoleAnd(roles) {
    return roles.every(item => {
      return authRole(item)
    })
  }
}
