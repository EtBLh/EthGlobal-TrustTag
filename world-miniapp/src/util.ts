export const shortenAddr = (addr: string) => {
  if (!addr || addr.length <= 12) return addr
  return `${addr.slice(0, 8)}...${addr.slice(-8)}`
}