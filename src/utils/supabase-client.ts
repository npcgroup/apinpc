import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const supabaseUrl = 'https://llanxjeohlxpnndhqbdp.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYW54amVvaGx4cG5uZGhxYmRwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2Mjg3ODAsImV4cCI6MjA1MDIwNDc4MH0.v3LyTKJAJ4ycRZBJ_rdCJSCvfEeqs-Ghk5gyDL-luI8';

if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseKey); 