import {
    Drawer,
    DrawerContent,
    DrawerFooter,
    DrawerHeader,
    DrawerTitle,
    DrawerTrigger
} from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import BackArrowIcon from '@/icons/backarrow.svg?react';
import { cn } from "@/lib/utils";
import { Link } from "react-router";
import { ProposalIcon } from "@/components/proposal-icon";
import { Badge } from "@/components/ui/badge"
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { createProposal } from "@/web3";

const SelectOption = (props: {
    title: string,
    description: string
    malicious?: boolean
    tagType: string
    onClick: (tag: string, malicious?: boolean) => void
}) => {
    return (
        <div className='flex flex-row items-center gap-2 w-full' onClick={() => {props.onClick(props.tagType, props.malicious)}}>
            <ProposalIcon type={props.tagType}/>
            <div className="flex flex-col items-start flex-1">
                <span>{props.title}</span>
                <span className="text-xs text-gray-200 text-left">{props.description}</span>
            </div>
            {
                props.malicious !== undefined ? (
                    <Badge variant="outline">
                        {props.malicious ? 'malicious' : 'non-malicious'}
                    </Badge>
                ) : null
            }
        </div>
    )
}

interface SelectProps {
    value: {
        tag: string,
        isMalicious: boolean
    }
    setValue: (val: string, malicious?: boolean) => void
}
const Select = (props: SelectProps) => {
    const [open, setOpen] = useState(false);
    const [customopen, setCustomOpen] = useState(false);
    const onOptionClick = (tag: string, malicious?: boolean) => {
        props.setValue(tag, malicious);
        setOpen(false);
    }
    return (
        <>
        <Drawer open={open} onOpenChange={setOpen}>
            <DrawerTrigger asChild>
                <div
                    className={cn(
                        "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input flex h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
                        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
                        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
                        "border-[2px] h-[48px] flex-row items-center gap-2"
                    )}
                >
                    <ProposalIcon type={props.value.tag} className="w-[28px] h-[28px]"/>
                    <span className="flex-1">
                        {props.value.tag}
                    </span>
                    {
                        props.value.isMalicious !== undefined &&
                            <Badge variant='outline'>
                                {
                                    props.value.isMalicious ? 'malicious' : 'non-malicious'
                                }
                            </Badge>
                    }
                </div>
            </DrawerTrigger>
            <DrawerContent className='flex items-start text-center w-full px-2 gap-3'>
                <DrawerHeader className="w-full">
                    <DrawerTitle>Select Tag</DrawerTitle>
                </DrawerHeader>
                <SelectOption 
                    tagType="normal_user"
                    title='Normal user'
                    description="Wallet for daily transactions"
                    malicious={false}
                    onClick={onOptionClick}
                />
                <SelectOption 
                    tagType="exchange"
                    title='Exchange'
                    description="Wallet holded by exchanges"
                    malicious={false}
                    onClick={onOptionClick}
                />
                <SelectOption 
                    tagType="gamble"
                    title='Gambling'
                    description="Wallet holded by gambling companies"
                    malicious={false}
                    onClick={onOptionClick}
                />
                <SelectOption 
                    tagType="scam"
                    title='Scam'
                    description="Wallet used for scamming"
                    malicious={true}
                    onClick={onOptionClick}
                />
                <SelectOption 
                    tagType="custom"
                    title='Customize'
                    description="customize your tag"
                    onClick={() => {
                        setOpen(false);
                        setCustomOpen(true);
                    }}
                />
                <DrawerFooter/>
            </DrawerContent>
        </Drawer>

        <Drawer open={customopen} onOpenChange={setCustomOpen}>
            <DrawerContent>
                <div className="px-4 py-2">                
                <span className='text-lg font-semibold'>Custom Tag</span>
                <div className="grid grid-cols-2 grid-rows-2 grid-cols-[3fr_1fr] grid-rows-[1fr_2fr] gap-x-2 gap-y-1 mt-2">
                    <span className="text-sm">Tag name</span>
                    <span className="text-sm">Malicious?</span>
                    <Input 
                        value={props.value.tag} 
                        onChange={e => props.setValue(e.target.value)}
                    />
                    <Switch 
                        className='transform-[scale(1.5)] ml-2 mt-2.5'
                        checked={props.value.isMalicious} 
                        onCheckedChange={(checked) => props.setValue(props.value.tag, checked)}
                    />
                </div>
                </div>
                <DrawerFooter>
                    <Button className="bg-indigo-500" onClick={() => setCustomOpen(false)}>Confirm</Button>
                </DrawerFooter>
            </DrawerContent>
        </Drawer>
        </>
    )
}

const ProposePage = () => {
    const [tag, setTag] = useState('normal_user');
    const [addr, setAddr] = useState('');
    const [proof, setProof] = useState('');
    const [isMalicious, setMalicious] = useState<boolean | undefined>(false);

    const onSubmit = async () => {
        const verifyPayload: VerifyCommandInput = {
            action: 'propose', // This is your action ID from the Developer Portal
            signal: addr, // Optional additional data
            verification_level: VerificationLevel.Orb, // Orb | Device
        }
        const { finalPayload } = await MiniKit.commandsAsync.verify(verifyPayload);
        if (finalPayload.status === 'error') {
			return console.log('Error payload', finalPayload)
		}
        await fetch(`${import.meta.env.VITE_API_URL}api/verify`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
                payload: finalPayload as ISuccessResult, // Parses only the fields we need to verify
                action: 'propose',
                signal: addr, // Optional
		    })
        });
        const id = await createProposal(addr, Boolean(isMalicious), tag);
        if (id === null) {
            console.log('id === null')
            return;
        }
        await fetch(`${import.meta.env.VITE_API_URL}api/propose`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: addr,
                tag: tag,
                proof: proof,
                malicious: Boolean(isMalicious)
            })
        })
    }

    return (
        <main className="flex flex-col relative flex-1">
            <header className='text-lg font-bold flex flex-row gap-1/2 items-center gap-2 px-4 py-2 border-b border-gray-600 fixed top-0 left-0 w-full h-[48px]'>
                <Link to='/home'>
                    <BackArrowIcon width={24} height={24} style={{ color: 'white' }} />
                </Link>
                <span className='text-xl montserrat font-normal absolute left-1/2 transform-[translateX(-50%)]'>Propose</span>
            </header>
            <div className='h-[48px]'></div>
            <section className="px-2 flex flex-col gap-2 py-4 flex-1">
                <div>
                    <span className="text-indigo-100 text-sm my-1">Tag</span>
                    <Select value={{tag, isMalicious}} setValue={(val, malicious) => {
                        setTag(val);
                        setMalicious(malicious);
                    }}/>
                </div>
                <div>
                    <span className="text-indigo-100 text-sm">Address</span>
                    <Input id="address" placeholder="0x123456...098765" className="h-[48px] border-[2px]" value={addr} onChange={(e) => setAddr(e.target.value)}/>
                </div>
                <div>
                    <span className="text-indigo-100 text-sm">Proof</span>
                    <Input id="proof" placeholder="https://etherscan.io/tx/0x7f5fb62.." className="h-[48px] border-[2px]" value={proof} onChange={(e) => setProof(e.target.value)}/>
                </div>
            </section>
            <Button className="bg-indigo-500 mx-2 mb-2 rounded-full" onClick={onSubmit}>Submit</Button>
        </main>
    )
}

export default ProposePage;