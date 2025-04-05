// AddressContext.tsx
import React, { createContext, useState, ReactNode, useContext } from "react";

type AddressContextType = {
  address: string;
  setAddress: (address: string) => void;
};

const AddressContext = createContext<AddressContextType | undefined>(undefined);

export const useAddress = () => {
  const context = useContext(AddressContext);
  if (!context) {
    throw new Error("useAddress must be used within AddressProvider");
  }
  return context;
};

export const AddressProvider = ({ children }: { children: ReactNode }) => {
  const [address, setAddress] = useState("");

  return (
    <AddressContext.Provider value={{ address, setAddress }}>
      {children}
    </AddressContext.Provider>
  );
};
