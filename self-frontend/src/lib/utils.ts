import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const shortenAddr = (addr: string) => {
  if (!addr || addr.length <= 12) return addr
  return `${addr.slice(0, 8)}...${addr.slice(-8)}`
}