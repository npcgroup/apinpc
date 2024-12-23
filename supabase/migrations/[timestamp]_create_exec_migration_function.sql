-- Create function to execute dynamic SQL
CREATE OR REPLACE FUNCTION public.exec_migration(sql text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.exec_migration(text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.exec_migration(text) TO service_role; 