export default function authHeader() {
  const storedUser = localStorage.getItem('openspending')
  const user = JSON.parse(storedUser || '{}')

  if (user && user.token) {
    return { Authorization: `Token ${user.token}` }
  } else {
    return {}
  }
}
