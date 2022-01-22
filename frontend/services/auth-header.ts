export default function authHeader() {
  const storedUser = localStorage.getItem('openspending')
  const user = JSON.parse(storedUser || '{}')

  if (user && user.token) {
    return { Authorization: user.token }
  } else {
    return {}
  }
}
