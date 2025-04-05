import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { useState } from "react"
import ClickAwayListener from 'react-click-away-listener';

function ProposeCard() {

  const [open, setOpen] = useState(false);

  return (
    <ClickAwayListener onClickAway={() => setOpen(false)}>
    <Card className="py-1 mt-4 mx-2" onClick={() => setOpen(true)}>
      <CardHeader className="px-3 py-1 border-b border-dotted">
        <CardTitle>Propse a Tag</CardTitle>
      </CardHeader>
      <CardContent className={cn('px-2 overflow-hidden transition-all duration-150 ease-in-out', open ? 'h-[200px]': 'h-[100px]')}>
        <div className="grid w-full items-center gap-4">
          <div className="flex flex-col space-y-1.5">
            {/* <Label htmlFor="name">Address</Label> */}
            <Input id="name" placeholder="Address" />
          </div>
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor="tag">Tag</Label>
            <Select>
              <SelectTrigger id="tag">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent position="popper">
                <SelectItem value="next">Scam</SelectItem>
                <SelectItem value="next">Exchange</SelectItem>
                <SelectItem value="next">Normal User</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button>Submit</Button>
      </CardContent>
    </Card>
    </ClickAwayListener>
  )
}

export default ProposeCard;